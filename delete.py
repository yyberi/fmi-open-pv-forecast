import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient
from influxdb_client.client.delete_api import DeleteApi

load_dotenv()

INFLUX_URL = os.getenv('INFLUX_URL')
INFLUX_TOKEN = os.getenv('INFLUX_TOKEN')
INFLUX_ORG = os.getenv('INFLUX_ORG')
INFLUX_BUCKET = os.getenv('INFLUX_BUCKET')


def delete_measurement(measurement_name):
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    delete_api = client.delete_api()

    # Define time range to delete all data for the measurement (start from epoch, end far in the future)
    start = "1970-01-01T00:00:00Z"
    stop = "2100-12-31T23:59:59Z"

    # Build predicate to match the measurement
    predicate = f'_measurement="{measurement_name}"'

    print(f"Deleting measurement '{measurement_name}' with predicate: {predicate}\nFrom {start} to {stop}")
    try:
        delete_api.delete(start, stop, predicate, bucket=INFLUX_BUCKET, org=INFLUX_ORG)
        print(f"Measurement '{measurement_name}' deleted from bucket '{INFLUX_BUCKET}'")
    except Exception as e:
        print(f"Error deleting measurement '{measurement_name}': {e}")
    finally:
        client.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python delete.py <measurement1> [<measurement2> ...]")
        sys.exit(1)

    for meas in sys.argv[1:]:
        delete_measurement(meas)
