"""Test Atlas using the small sample read back from Spark and Cassandra."""
import json
from getpass import getpass
from pathlib import Path
from pymongo import MongoClient, ReplaceOne


def main():
    # Enter the password locally. It is never saved in this file or printed.
    password = getpass('MongoDB password for ind320_user: ')
    with MongoClient(
        'mongodb+srv://ind320.t7alwpp.mongodb.net/?appName=IND320',
        username='ind320_user', password=password,
        serverSelectionTimeoutMS=15000,
    ) as client:
        client.admin.command('ping')
        print('MongoDB connection successful.')
        path = Path(__file__).parent / 'setup_sample.json'
        if not path.exists():
            print('Run test_spark_cassandra.py first to prepare the sample.')
            return
        records = json.loads(path.read_text())
        collection = client['ind320_setup']['nve_sample']
        # Stable IDs let us repeat the test without inserting duplicates.
        collection.bulk_write([
            ReplaceOne({'_id': row['_id']}, row, upsert=True) for row in records
        ])
        actual = list(collection.find({'_id': {'$in': [r['_id'] for r in records]}}).sort('_id', 1))
        assert actual == records, 'The values read back differ from the sample.'
        print(f'PASS: {len(actual)} observations written to Atlas and read back unchanged.')


if __name__ == '__main__':
    main()
