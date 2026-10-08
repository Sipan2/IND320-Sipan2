"""Move validated physical flows through Spark, Cassandra and MongoDB."""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def build_curated():
    # UTC prevents daylight-saving changes from shifting interval boundaries.
    os.environ['PYSPARK_PYTHON'] = sys.executable
    os.environ['SPARK_LOCAL_IP'] = '127.0.0.1'
    if sys.platform == 'darwin':
        import subprocess
        os.environ['JAVA_HOME'] = subprocess.check_output(
            ['/usr/libexec/java_home', '-v', '17'], text=True).strip()
    from cassandra.cluster import Cluster
    from pyspark.sql import SparkSession, functions as F
    from prepare_transfers import prepare
    source, coverage = prepare()
    cluster = Cluster(['127.0.0.1'], port=9042)
    spark = None
    try:
        session = cluster.connect()
        session.execute("CREATE KEYSPACE IF NOT EXISTS ind320 WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1}")
        session.execute("""CREATE TABLE IF NOT EXISTS ind320.physical_flows (
            connection text, direction text, month text, start_utc text, end_utc text,
            power_mw double, energy_mwh double, resolution_minutes int, curve_type text,
            PRIMARY KEY ((connection, direction, month), start_utc))""")
        spark = (SparkSession.builder.master('local[2]').appName('IND320 electricity transfers')
            .config('spark.jars.packages', 'com.datastax.spark:spark-cassandra-connector_2.12:3.5.1')
            .config('spark.jars.ivy', str(ROOT / '.ivy2'))
            .config('spark.cassandra.connection.host', '127.0.0.1')
            .config('spark.sql.session.timeZone', 'UTC')
            .config('spark.sql.shuffle.partitions', '8')
            .config('spark.ui.enabled', 'false')
            .config('spark.ui.showConsoleProgress', 'false').getOrCreate())
        spark.sparkContext.setLogLevel('ERROR')
        schema = ('connection string, direction string, month string, start_utc string, '
                  'end_utc string, power_mw double, energy_mwh double, '
                  'resolution_minutes int, curve_type string')
        raw = spark.read.schema(schema).json(str(source))
        expected = raw.count()
        raw.write.format('org.apache.spark.sql.cassandra').options(
            keyspace='ind320', table='physical_flows').mode('append').save()
        # Read back from Cassandra, rather than forwarding the input DataFrame.
        selected = (spark.read.format('org.apache.spark.sql.cassandra').options(
            keyspace='ind320', table='physical_flows').load()
            .filter((F.col('month') >= '2024-10') & (F.col('month') <= '2026-09'))
            .select('connection', 'direction', 'start_utc', 'end_utc', 'power_mw', 'energy_mwh'))
        if selected.count() != expected:
            raise ValueError('The Cassandra read-back count differs from the input.')
        # Keep hourly energy and observed duration. Partial hours remain flagged.
        timed = selected.withColumn('start', F.to_timestamp('start_utc')).withColumn('end', F.to_timestamp('end_utc'))
        timed = timed.withColumn('hours', (F.col('end').cast('long') - F.col('start').cast('long')) / 3600)
        if timed.filter((F.col('hours') <= 0) | (F.col('hours') > 1) | (F.col('end').cast('long') > F.date_trunc('hour', F.col('start')).cast('long') + 3600)).limit(1).count():
            raise ValueError('The hourly aggregation needs intervals of at most one hour.')
        hourly = (timed.groupBy('connection', 'direction', F.date_trunc('hour', 'start').alias('start_utc'))
            .agg(F.sum('energy_mwh').alias('energy_mwh'), F.sum('hours').alias('observed_hours'))
            .withColumn('power_mw', F.col('energy_mwh') / F.col('observed_hours'))
            .withColumn('end_utc', F.expr('start_utc + INTERVAL 1 HOUR')))
        if hourly.filter(F.col('observed_hours') > 1.000001).limit(1).count():
            raise ValueError('An hour contains overlapping observations.')
        # Format timestamps in Spark's UTC session before collecting them.
        # Python's local timezone must not shift the stored clock times.
        hourly = hourly.withColumn('start_utc', F.date_format('start_utc', "yyyy-MM-dd'T'HH:mm:ss"))\
                       .withColumn('end_utc', F.date_format('end_utc', "yyyy-MM-dd'T'HH:mm:ss"))
        folder = ROOT / 'entsoe_raw'
        count = 0
        with (folder / 'curated.jsonl').open('w') as output:
            for row in hourly.orderBy('connection', 'direction', 'start_utc').toLocalIterator():
                record = row.asDict()
                for name in ('start_utc', 'end_utc'):
                    record[name] = record[name] + '+00:00'
                output.write(json.dumps(record) + '\n')
                count += 1
        result = dict(raw_intervals=expected, curated_hours=count,
                      incomplete_months=sum(r['observed_hours'] != r['expected_hours'] for r in coverage))
        (folder / 'pipeline_result.json').write_text(json.dumps(result, indent=2))
        print(result)
        return result
    finally:
        if spark is not None:
            spark.stop()
        cluster.shutdown()


def upload_curated(password):
    from pymongo import MongoClient, ReplaceOne
    # The write credential stays in memory. Streamlit has a separate read-only user.
    client = MongoClient('mongodb+srv://ind320.t7alwpp.mongodb.net/?appName=IND320',
                         username='ind320_user', password=password, serverSelectionTimeoutMS=15000,
                         connectTimeoutMS=15000, socketTimeoutMS=60000, timeoutMS=90000)
    try:
        print('Connecting to MongoDB...', flush=True)
        client.admin.command('ping')
        print('Authentication confirmed. Uploading hourly records...', flush=True)
        collection = client['ind320']['transfers']
        operations = []
        count = 0
        with (ROOT / 'entsoe_raw' / 'curated.jsonl').open() as source:
            for line in source:
                row = json.loads(line)
                row['_id'] = '|'.join([row['connection'], row['direction'], row['start_utc']])
                operations.append(ReplaceOne({'_id': row['_id']}, row, upsert=True))
                count += 1
                if len(operations) == 1000:
                    collection.bulk_write(operations, ordered=False)
                    operations.clear()
                    print(f'Uploaded records: {count}', flush=True)
            if operations:
                collection.bulk_write(operations, ordered=False)
        print(f'Upload complete: {count}. Checking database count...', flush=True)
        actual = collection.count_documents({'start_utc': {'$gte': '2024-09-30T22:00:00', '$lt': '2026-09-30T22:00:00'}})
        if actual != count:
            raise ValueError('MongoDB read-back count differs from the curated data.')
        (ROOT / 'entsoe_raw' / 'mongodb_result.json').write_text(json.dumps({'verified_observations': actual}, indent=2))
        print('Verified MongoDB observations:', actual)
        return actual
    finally:
        client.close()


if __name__ == '__main__':
    build_curated()
    from getpass import getpass
    upload_curated(getpass('MongoDB password for ind320_user: '))
