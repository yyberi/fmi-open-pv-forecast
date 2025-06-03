import datetime
import pandas as pd
import config
from helpers import solar_irradiance_estimator, irradiance_transpositions, reflection_estimator, panel_temperature_estimator, output_estimator


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

    # Adjust timestamps to exact hours (using lowercase 'h' to avoid FutureWarning)
    data['endTime'] = data['time'].dt.ceil('h')
    data['startTime'] = data['endTime'] - pd.Timedelta(hours=1)

    # Rearrange columns
    cols = ['startTime', 'endTime'] + [col for col in data.columns if col not in ['time', 'startTime', 'endTime']]
    data = data[cols]

    return data


if __name__ == '__main__':
    forecast_data = generate_forecast()
    forecast_data.to_csv('output/forecast.csv', float_format='%.2f', index=False)