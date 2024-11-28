import datetime
import time

import pandas
import config
import helpers.irradiance_transpositions
import plotter
from helpers import solar_irradiance_estimator, astronomical_calculations
from helpers import reflection_estimator
from helpers import panel_temperature_estimator
from helpers import output_estimator

import pandas as pd

"""
Main file, contains examples on how to call the functions from other files.

Modify parameters in file config.py in order to change the simulated installation location and other installation 
parameters.

full_processing_of_fmi_open_data()
-generates solar pv forecast data with fmi open and plots a minimal plot

full_processing_of_pvlib_open_data()
-generates solar pv forecast data with pvlib and plots a minimal plot

get_fmi_data(day_range)
-generates a power generation dataframe by using fmi open

get_pvlib_data(day_range)
-generates a power generation dataframe by using pvlib

combined_processing_of_data()
-used get_fmi_data and get_pvlib_data to generate dataframes. Plots the data with plotter monoplot.
plot shows power(W) and energy(kWh) values for each day.

Author: TimoSalola (Timo Salola).
"""

def print_full(x: pandas.DataFrame):
    """
    Prints a dataframe without leaving any columns or rows out. Useful for debugging.
    """

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1400)
    pd.set_option('display.float_format', '{:10,.2f}'.format)
    pd.set_option('display.max_colwidth', None)
    print(x)
    pd.reset_option('display.max_rows')
    pd.reset_option('display.max_columns')
    pd.reset_option('display.width')
    pd.reset_option('display.float_format')
    pd.reset_option('display.max_colwidth')

def full_processing_of_fmi_open_data():
    # date for simulation:
    today = datetime.date.today()
    date_start = datetime.datetime(today.year, today.month, today.day)

    # step 1. simulate irradiance components dni, dhi, ghi:
    data = solar_irradiance_estimator.get_solar_irradiance(date_start, day_count=3, model="fmiopen")

    # step 2. project irradiance components to plane of array:
    data = helpers.irradiance_transpositions.irradiance_df_to_poa_df(data)

    # step 3. simulate how much of irradiance components is absorbed:
    data = helpers.reflection_estimator.add_reflection_corrected_poa_components_to_df(data)

    # step 4. compute sum of reflection-corrected components:
    data = helpers.reflection_estimator.add_reflection_corrected_poa_to_df(data)

    # step 5. estimate panel temperature based on wind speed, air temperature and absorbed radiation
    data = helpers.panel_temperature_estimator.add_estimated_panel_temperature(data)

    # step 6. estimate power output
    data = helpers.output_estimator.add_output_to_df(data)

    # printing and plotting data
    print_full(data)

    plotter.init_plot()
    plotter.add_label_x("Time")
    plotter.add_label_y("Output(W)")
    plotter.add_title("Simulated solar PV system output")
    plotter.plot_curve(data["time"], data["output"], label="Output(W)")
    plotter.plot_kwh_labels(data)
    plotter.show_legend()
    plotter.show_plot()


def full_processing_of_pvlib_data():


    # date for simulation:
    today = datetime.date.today()
    date_start = datetime.datetime(today.year, today.month, today.day)

    # step 1. simulate irradiance components dni, dhi, ghi:
    data = solar_irradiance_estimator.get_solar_irradiance(date_start, day_count=3, model="pvlib")

    # step 2. project irradiance components to plane of array:
    data = helpers.irradiance_transpositions.irradiance_df_to_poa_df(data)

    # step 3. simulate how much of irradiance components is absorbed:
    data = helpers.reflection_estimator.add_reflection_corrected_poa_components_to_df(data)

    # step 4. compute sum of reflection-corrected components:
    data = helpers.reflection_estimator.add_reflection_corrected_poa_to_df(data)

    # step 4.1. add dummy wind and air temp data
    data = helpers.panel_temperature_estimator.add_dummy_wind_and_temp(data, config.wind_speed, config.air_temp)

    # step 5. estimate panel temperature based on wind speed, air temperature and absorbed radiation
    data = helpers.panel_temperature_estimator.add_estimated_panel_temperature(data)

    # step 6. estimate power output
    data = helpers.output_estimator.add_output_to_df(data)

    # printing and plotting data
    print_full(data)

    plotter.init_plot()
    plotter.add_label_x("Time")
    plotter.add_label_y("Output(W)")
    plotter.add_title("Simulated solar PV system output")
    plotter.plot_curve(data["time"], data["output"], label="Output(W)")
    plotter.plot_kwh_labels(data)
    plotter.show_legend()
    plotter.show_plot()


def get_fmi_data(day_range=3):
    """
    This function shows the steps used for generating power output data with fmi open. Also returns the power output.
    Note that FMI open only gives irradiance estimates for the next ~64 hours.
    :param day_range: Day count, 1 returns only this day, 3 returns this day and the 2 following days.
    :return: Power output dataframe
    """

    # using a temporary override of data resolution as fmi open operates on 60 minute data sections.
    # saving original data resolution
    original_data_resolution = config.data_resolution
    # setting temporary value for fmi data processing(this is restored back to original value later)
    config.data_resolution = 60

    # date for simulation:
    today = datetime.date.today()
    date_start = datetime.datetime(today.year, today.month, today.day)

    # step 1. simulate irradiance components dni, dhi, ghi:
    data = solar_irradiance_estimator.get_solar_irradiance(date_start, day_count=day_range, model="fmiopen")

    # step 2. project irradiance components to plane of array:
    data = helpers.irradiance_transpositions.irradiance_df_to_poa_df(data)

    # step 3. simulate how much of irradiance components is absorbed:
    data = helpers.reflection_estimator.add_reflection_corrected_poa_components_to_df(data)

    # step 4. compute sum of reflection-corrected components:
    data = helpers.reflection_estimator.add_reflection_corrected_poa_to_df(data)

    # step 5. estimate panel temperature based on wind speed, air temperature and absorbed radiation
    data = helpers.panel_temperature_estimator.add_estimated_panel_temperature(data)

    # step 6. estimate power output
    data = helpers.output_estimator.add_output_to_df(data)

    config.data_resolution = original_data_resolution

    return data


def get_pvlib_data(day_range=3, data_fmi=None):
    """
    This function shows the steps used for generating power output data with pvlib. Also returns the power output.
    PVlib is fully simulated, no restrictions on day range.
    :param day_range: Day count, 1 returns only this day, 3 returns this day and the 2 following days.
    :param data_fmi: If fmi df is given here, it will be used as weather data donor df
    :return: Power output dataframe
    """
    # date for simulation:
    today = datetime.date.today()
    date_start = datetime.datetime(today.year, today.month, today.day)

    data_pvlib = solar_irradiance_estimator.get_solar_irradiance(date_start, day_count=day_range, model="pvlib")

    # step 2. project irradiance components to plane of array:
    data_pvlib = helpers.irradiance_transpositions.irradiance_df_to_poa_df(data_pvlib)

    # step 3. simulate how much of irradiance components is absorbed:
    data_pvlib = helpers.reflection_estimator.add_reflection_corrected_poa_components_to_df(data_pvlib)

    # step 4. compute sum of reflection-corrected components:
    data_pvlib = helpers.reflection_estimator.add_reflection_corrected_poa_to_df(data_pvlib)

    # step 4.1. adding wind and air speed to dataframe
    if data_fmi is not None:
        # getting data from fmi dataframe if one was given
        data_pvlib = panel_temperature_estimator.add_wind_and_temp_to_df1_from_df2(data_pvlib, data_fmi)
    else:
        # using dummy values if no df was given
        data_pvlib = helpers.panel_temperature_estimator.add_dummy_wind_and_temp(data_pvlib, config.wind_speed, config.air_temp)

    # step 5. estimate panel temperature based on wind speed, air temperature and absorbed radiation
    data_pvlib = helpers.panel_temperature_estimator.add_estimated_panel_temperature(data_pvlib)

    # step 6. estimate power output
    data_pvlib = helpers.output_estimator.add_output_to_df(data_pvlib)

    data_pvlib = data_pvlib.dropna()

    return data_pvlib


def combined_processing_of_data():
    """
    Uses both pvlib and fmi open to compute solar irradiance for the next 4 days and plots both
    :return:
    """

    day_range = 3

    print("Simulating clear sky and weather model based PV generation for the next " + str(day_range) +" days.")
    # fetching fmi data and generating solar pv output df

    data_fmi = get_fmi_data(day_range)

    # generating pvlib irradiance values and clear sky pv dataframe, passing fmi data to pvlib generator functions
    # for wind and air temp transfer
    data_pvlib = get_pvlib_data(day_range, data_fmi)


    # this line prints the full results into console/terminal

    if config.console_print:
        print("-------------------------------------------------------------------------------------------------------")
        print("Output table printing is turned on in the config.py file")
        print("-----Data-----")

        print_full(data_fmi)

        print("-----Columns explained-----")
        print(
            "[index(Time)]: Meteorological time. In meteorology, timestamp for 13:00 represents the time 12:00-13:00.")
        print("[time]: This is time index shifted by 30min. More useful than the meteorological time for physics.")
        print("[dni, dhi, ghi]: Irradiance types, these can be used for estimating radiation from direct radiation,"
              " atmosphere scattered radiation and ground reflected radiation.")
        print("[albedo]: Ground reflectivity near installation. This is retrieved from fmi open data service. Should be"
              "between 0 and 1.")
        print("[T]: Air temperature at 2m.")
        print("[wind]: Wind speed at 2m.")
        print("[cloud_cover]: Cloudiness percentage, between 0 and 100.")
        print("[dni_poa, dhi_poa, ghi_poa]: Transpositions of dni, dhi and ghi to the plane of array(POA). These values"
              " are always positive and lower than their non _poa counterparts.")
        print("[poa]: Sum of dni_poa, dhi_poa, ghi_poa. Represents the amount of radiation reaching the panel surface."
              " This does not account for panel reflectivity.")
        print("[dni_rc, dhi_rc, ghi_rc]: Transpositions of radiation types with reflection corrections. These are lower"
              "than their '_poa' counterparts.")
        print("[poa_ref_cor]: Sum of dni_rc, dhi_rc and ghi_rc. This represents the amount of radiation absorbed by the"
              " solar panels.")
        print(
            "[module_temp]: Estimated value for solar panel temperature. Based on air temp, wind speed and radiation.")
        print("[output]: System output in watts.")
        print("Note that all values before [output] are for a simulated theoretical 1m² panel.")
        print("-------------------------------------------------------------------------------------------------------")

    # this line saves the results as a csv file
    if config.save_csv:
        print("-------------------------------------------------------------------------------------------------------")
        print("Output table csv exporting is turned on in the config.py file")
        filename = config.save_directory+ config.site_name + str(datetime.date.today()) + ".csv"
        data_fmi.to_csv(filename,float_format='%.2f')
        print("Saved csv as: " + filename)
        print("-------------------------------------------------------------------------------------------------------")


    plotter.plot_fmi_pvlib_mono(data_fmi, data_pvlib)



combined_processing_of_data()

