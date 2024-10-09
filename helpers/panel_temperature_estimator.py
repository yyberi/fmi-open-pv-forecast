"""
This file contains functions for estimating PV panel temperatures and transferring temperature data from another
dataframe.

Author: TimoSalola (Timo Salola).
"""
import math
from datetime import timedelta
import pandas
import config


def add_estimated_panel_temperature(df:pandas.DataFrame)-> pandas.DataFrame:
    """
    Adds an estimate for panel temperature based on wind speed, air temperature and absorbed radiation.
    If air temperature, wind speed or absorbed radiation columns are missing, aborts.
    If columns exists but temperature function returns nan due to faulty input, uses air temperature which should always
    be present in df.
    :param df:
    :return:

    """

    # checking that all required variables exist in df

    if "T" not in df.columns:
        print("No air temperature variable in given dataframe")
        print("Aborting")
        return df

    if "wind" not in df.columns:
        print("No wind speed variable in given dataframe")
        print("Aborting")
        return df

    if "poa_ref_cor" not in df.columns:
        print("no reflection corrected poa value in df 'poa_ref_cor'")
        print("Aborting")
        return df

    def helper_add_panel_temp(df):
        estimated_temp = temperature_of_module(df["poa_ref_cor"], df["wind"], config.module_elevation, df["T"])
        if math.isnan(estimated_temp):
            return df["T"]
        else:
            return estimated_temp

    # applying helper function to dataset and storing result as a new column
    df["module_temp"] = df.apply(helper_add_panel_temp, axis=1)

    return df


def add_dummy_wind_and_temp(df:pandas.DataFrame, wind=2, temp=20)-> pandas.DataFrame:
    """
    Adds dummy wind speed and air temperature values. 20 Celsius and 2 m/s wind by default.
    :param df:
    :param wind:
    :param temp:
    :return: input df with wind and air temp columns with dummy values
    """

    if "T" not in df.columns:
        df = add_dummy_temperature(df, temp)

    if "wind" not in df.columns:
        df = add_dummy_wind(df, wind)

    return df


def add_dummy_temperature(df: pandas.DataFrame, temp=20)->pandas.DataFrame :
    df["T"] = temp
    return df


def add_dummy_wind(df, wind=2):
    df["wind"] = wind
    return df


def add_wind_and_temp_to_df1_from_df2(df1: pandas.DataFrame, df2: pandas.DataFrame):
    """
    This function assumes that df2 has wind and temp info which can be transferred to df1
    :param df1: target df, pvlib generated multi day df
    :param df2: donor df, fmi open generated multi day df
    :return: target df with wind and T columns which are from df2
    """

    # If df1 does not have values where minute == 30, the frames do not align well. Can cause issues.
    # alignment issues can be avoided by using config.data_resolution of 60, 30, 15, 10, 5, 1

    # creating weather df
    weather_df = df2[["time", "wind", "T"]]

    # joining weather df to df1
    df1 = df1.merge(weather_df, on="time", how="outer")

    # filling in nan values for wind
    df1['wind'] = df1['wind'].interpolate(limit_direction='both')

    # filling in nan values for temp
    df1['T'] = df1['T'].interpolate(limit_direction='both')

    return df1


def temperature_of_module(absorbed_radiation: float, wind: float, module_elevation: float, air_temperature: float) ->float:
    """
    :param absorbed_radiation: radiation hitting solar panel after reflections are accounted for in W
    :param wind: wind speed in meters per second
    :param module_elevation: module elevation from ground, in meters
    :param air_temperature: air temperature at 2m in Celsius
    :return: module temperature in Celsius

    King 2004 model
    D.~King, J.~Kratochvil, and W.~Boyson,
    Photovoltaic Array Performance Model Vol. 8,
    PhD thesis (Sandia Naitional Laboratories, 2004).
    """

    # two empirical constants
    constant_a = -3.47
    constant_b = -0.0594

    # wind is sometimes given as west/east components

    # wind speed at model elevation, assumes 0 speed at ground, wind speed vector len at 2m and forms a
    # curve which describes the wind speed transition from 0 to 10m wind speed to higher
    wind_speed = (module_elevation / 10) ** 0.1429 * wind

    module_temperature = absorbed_radiation * math.e ** (constant_a + constant_b * wind_speed) + air_temperature

    return module_temperature
