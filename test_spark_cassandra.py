"""Check the local database setup using a small sample of real NVE data."""
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.request import urlopen

from cassandra.cluster import Cluster
from pyspark.sql import SparkSession

# Use the same Python interpreter for Spark workers and the notebook.
os.environ['PYSPARK_PYTHON'] = sys.executable
os.environ['SPARK_LOCAL_IP'] = '127.0.0.1'
if sys.platform == 'darwin':
    os.environ['JAVA_HOME'] = subprocess.check_output(
        ['/usr/libexec/java_home', '-v', '17'], text=True).strip()


def main():
    # This small table tests the connection; it is not the ENTSO-E analysis.
    with urlopen('https://biapi.nve.no/magasinstatistikk/api/Magasinstatistikk/HentOffentligData', timeout=60) as response:
        raw = json.load(response)
    sample = sorted(
        [r for r in raw if r['omrType'] == 'NO' and r['omrnr'] == 0],
        key=lambda r: r['dato_Id'])[-12:]
    records = [(r['dato_Id'][:10], float(r['fyllingsgrad'])) for r in sample]
    cluster = Cluster(['127.0.0.1'], port=9042)
    spark = None
    try:
        session = cluster.connect()
        session.execute("CREATE KEYSPACE IF NOT EXISTS ind320_setup WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}")
        session.execute('CREATE TABLE IF NOT EXISTS ind320_setup.nve_sample (date text PRIMARY KEY, filling_ratio double)')
        spark = (SparkSession.builder.master('local[2]').appName('IND320 setup check')
                 .config('spark.jars.packages', 'com.datastax.spark:spark-cassandra-connector_2.12:3.5.1')
                 .config('spark.jars.ivy', str(Path(__file__).parent / '.ivy2'))
                 .config('spark.cassandra.connection.host', '127.0.0.1')
                 .config('spark.cassandra.connection.port', '9042')
                 .config('spark.ui.enabled', 'false').getOrCreate())
        spark.sparkContext.setLogLevel('ERROR')
        frame = spark.createDataFrame(records, 'date string, filling_ratio double')
        frame.write.format('org.apache.spark.sql.cassandra').options(
            keyspace='ind320_setup', table='nve_sample').mode('append').save()
        # Primary keys make repeated writes update the same dates.
        result = (spark.read.format('org.apache.spark.sql.cassandra').options(
            keyspace='ind320_setup', table='nve_sample').load()
            .filter(f"date >= '{records[0][0]}' AND date <= '{records[-1][0]}'")
            .select('date', 'filling_ratio').orderBy('date'))
        actual = [(r.date, r.filling_ratio) for r in result.collect()]
        assert actual == records, 'The values read back differ from the input.'
        result.show(12, truncate=False)
        # This small export can test MongoDB without downloading ENTSO-E data.
        target = Path(__file__).parent / 'setup_sample.json'
        target.write_text(json.dumps([{'_id': d, 'filling_ratio': v} for d, v in actual], indent=2))
        print('PASS: 12 NVE observations written and read back through Spark and Cassandra.')
    finally:
        if spark is not None:
            spark.stop()
        cluster.shutdown()


if __name__ == '__main__':
    main()
