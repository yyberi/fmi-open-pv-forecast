import datetime
import pandas as pd
import config
import os
from dotenv import load_dotenv, find_dotenv
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from helpers import solar_irradiance_estimator, irradiance_transpositions, reflection_estimator, panel_temperature_estimator, output_estimator

# Load .env from project root
load_dotenv(find_dotenv())

INFLUX_URL = os.getenv('INFLUX_URL')
INFLUX_TOKEN = os.getenv('INFLUX_TOKEN')
INFLUX_ORG = os.getenv('INFLUX_ORG')
INFLUX_BUCKET = os.getenv('INFLUX_BUCKET')

# Debug: print environment values
print(f"Connecting to InfluxDB with URL={INFLUX_URL}, ORG={INFLUX_ORG}, BUCKET={INFLUX_BUCKET}")
if not all([INFLUX_URL, INFLUX_TOKEN, INFLUX_ORG, INFLUX_BUCKET]):
    raise EnvironmentError("Missing one or more InfluxDB env variables. Check .env file.")


def generate_forecast(day_range=3):
    original_resolution = config.data_resolution
    config.data_resolution = 60

    today = datetime.date.today()
    date_start = datetime.datetime(today.year, today.month, today.day)

    data = solar_irradiance_estimator.get_solar_irradiance(date_start, day_count=day_range, model="fmiopen")
    data = irradiance_transpositions.irradiance_df_to_poa_df(data)
    data = reflection_estimator.add_reflection_corrected_poa_components_to_df(data)
    data = reflection_estimator.add_reflection_corrected_poa_to_df(data)
    data = panel_temperature_estimator.add_estimated_panel_temperature(data)
    data = output_estimator.add_output_to_df(data)

    config.data_resolution = original_resolution

    # Adjust timestamps to exact hours
    data['endTime'] = data['time'].dt.ceil('h')
    data['startTime'] = data['endTime'] - pd.Timedelta(hours=1)

    # Rearrange columns
    cols = ['startTime', 'endTime'] + [col for col in data.columns if col not in ['time', 'startTime', 'endTime']]
    data = data[cols]

    return data


def write_to_influx(data, measurement):
    print(f"Initializing write to measurement '{measurement}' with {len(data)} points")
    try:
        client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
        health = client.health()
        if health.status != 'pass':
            print(f"InfluxDB health check failed: {health.status} Message: {health.message}")
            client.close()
            return
        print(f"InfluxDB health status: {health.status}")
        # Override signout to avoid __del__ warning
        try:
            client.api_client._signout = lambda *args, **kwargs: None
        except AttributeError:
            pass
        write_api = client.write_api(write_options=SYNCHRONOUS)
    except Exception as conn_err:
        print(f"Cannot connect to InfluxDB at {INFLUX_URL}: {conn_err}")
        return

    for i, row in enumerate(data.itertuples(), start=1):
        point = Point(measurement)
        for col in data.columns:
            if col not in ['startTime', 'endTime']:
                value = getattr(row, col)
                if pd.notna(value):
                    point.field(col, float(value))
        point.time(row.endTime, WritePrecision.S)
        try:
            write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
        except Exception as e:
            print(f"Error writing point {i} to measurement '{measurement}': {e}")

    client.close()


if __name__ == '__main__':
    config.set_params_custom()
    forecast_data = generate_forecast()

    # Convert output column from Watts to kilowatts
    if 'output' in forecast_data.columns:
        forecast_data['output'] = forecast_data['output'] / 1000.0

    # Filter out rows older than now
    now = pd.Timestamp.utcnow()
    forecast_data = forecast_data[forecast_data['endTime'] > now]

    # Save to CSV
    forecast_data.to_csv('output/forecast.csv', float_format='%.2f', index=False)

    # Write to measurements
    write_to_influx(forecast_data, 'pv_forecast')
    tomorrow = forecast_data[forecast_data['startTime'].dt.date == (datetime.date.today() + datetime.timedelta(days=1))]
    write_to_influx(tomorrow, 'pv_forecast_1d')
    day_after = forecast_data[forecast_data['startTime'].dt.date == (datetime.date.today() + datetime.timedelta(days=2))]
    write_to_influx(day_after, 'pv_forecast_2d')
