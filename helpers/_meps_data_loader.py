"""
This file retrieves irradiance values from FMI open API
Information on the service can be found here:
https://en.ilmatieteenlaitos.fi/open-data-manual-forecast-models

Data is available for a 66-hour period
Data updates every 3 hours starting from 00 UTC, slight variation in timing can occur
Data usually contains a couple of hours of historical data due to delays in running and transferring weather model data
between services before the forecast becomes available.

Author: kalliov (Viivi Kallio).
Modifications by: TimoSalola (Timo Salola).
"""
import time
import datetime as dt
from datetime import datetime
import pandas
import pandas as pd
import numpy as np
from fmiopendata.wfs import download_stored_query
from helpers import astronomical_calculations


def collect_fmi_opendata(latlon: str, start_time:datetime, end_time:datetime)-> pandas.DataFrame:
    """
    :param latlon:      str(latitude) + "," + str(longitude)
    :param start_time:  2013-03-05T12:00:00Z ISO TIME
    :param end_time:    2013-03-05T12:00:00Z ISO TIME
    :return: Pandas dataframe with columns ["time", "dni", "dhi", "ghi", "dir_hi", "albedo", "T", "wind", "cloud_cover"]
    """


    collection_string = "fmi::forecast::harmonie::surface::point::multipointcoverage"

    # List the wanted MEPS parameters
    parameters = ["Temperature",
                  "RadiationGlobalAccumulation",
                  "RadiationNetSurfaceSWAccumulation",
                  "RadiationSWAccumulation",
                  "WindSpeedMS",
                  "TotalCloudCover"
                  ]
    parameters_str = ','.join(parameters)

    # Collect data
    snd = download_stored_query(collection_string,
                                args=["latlon=" + latlon,
                                      "starttime=" + str(start_time),
                                      "endtime=" + str(end_time),
                                      'parameters=' + parameters_str])
    data = snd.data



    # Times to use in forming dataframe
    data_list = []
    # Make the dict of dict of dict of.. into pandas dataframe
    for time_a, location_data in data.items():
        location = list(location_data.keys())[0]  # Get the location dynamically
        values = location_data[location]

        data_list.append({'Time': time_a,
                          'T': values['Air temperature']['value'],
                          'GHI_accum': values['Global radiation accumulation']['value'],
                          'NetSW_accum': values['Net short wave radiation accumulation at the surface']['value'],
                          'DirHI_accum': values['Short wave radiation accumulation']['value'],
                          'Wind speed': values['Wind speed']['value'],
                          'Total cloud cover': values['Total cloud cover']['value']})

    # Create a DataFrame and set time as index   
    df = pd.DataFrame(data_list)
    df.set_index('Time', inplace=True)

    # Calculate instant from accumulated values (only radiation parameters)
    diff = df.diff()
    df['GHI'] = diff['GHI_accum'] / (60 * 60)
    df['NetSW'] = diff['NetSW_accum'] / (60 * 60)
    df['DirHI'] = diff['DirHI_accum'] / (60 * 60)
    # GHI = grad_instant
    # DirHI = swavr_instant
    # netSW = nswrs_instant

    # Calculate albedo (refl/ghi), refl=ghi-net
    df['albedo'] = (df['GHI'] - df['NetSW']) / df['GHI']

    # restricting abledo to be within range of 0 to 1
    df['albedo'] = df['albedo'].mask(~df['albedo'].between(0, 1))

    # setting all nan values to mean of known values
    df['albedo'] = df['albedo'].fillna(df['albedo'].mean())

    # Calculate Diffuse horizontal from global and direct
    df['DHI'] = df['GHI'] - df['DirHI']
    #

    # Adding solar zenith angle to df
    df["time"] = df.index
    df["sza"] = astronomical_calculations.get_solar_azimuth_zenit_fast(df["time"])[1]
    # solar zenit angle added

    # Calculate dni from dhi
    df['DNI'] = df['DirHI'] / np.cos(df['sza'] * (np.pi / 180))

    # Keep the necessary parameters
    df = df[['DNI', 'DHI', 'GHI', 'DirHI', 'albedo',
             'T', 'Wind speed', 'Total cloud cover']]

    df.columns = ["dni", "dhi", "ghi", "dir_hi", "albedo", "T", "wind", "cloud_cover"]

    df.insert(loc=0, column="time", value=df.index)

    # shifting timestamps to time-interval centers as timestamp for 12:00 refers to average during 11:00-12:00
    df["time"] = df["time"] + dt.timedelta(minutes=-30)
    # adding utc timezone marker to time
    df["time"] = df["time"].dt.tz_localize("UTC")

    # restricting values to zero
    clip_columns = ["dni", "dhi", "ghi"]
    df[clip_columns] = df[clip_columns].clip(lower=0.0)
    df.replace(-0.0, 0.0, inplace=True)

    return (df)
