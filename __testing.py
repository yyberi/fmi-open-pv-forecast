import datetime
import time

import pandas
import config
import helpers.irradiance_transpositions
import main
import plotter
from helpers import solar_irradiance_estimator, astronomical_calculations
from helpers import reflection_estimator
from helpers import panel_temperature_estimator
from helpers import output_estimator

import pandas as pd

from main import get_fmi_data

"""
This file contains functions for development testing of the program.
"""


def __timed_combined_processing_of_data():
    """
    Testing function for evaluating the combined plot generation time.
    Total time 0.477
    Time fmi 0.127
    Time pvlib 0.027
    Time plotting 0.319
    """

    day_range = 3

    print("Simulating clear sky and weather model based PV generation for the next " + str(day_range) +" days.")
    # fetching fmi data and generating solar pv output df

    time0 = time.time()
    data_fmi = get_fmi_data(day_range)

    time1 = time.time()

    # generating pvlib irradiance values and clear sky pv dataframe, passing fmi data to pvlib generator functions
    # for wind and air temp transfer
    data_pvlib = main.get_pvlib_data(day_range, data_fmi)

    time2 = time.time()

    # this line prints the full results into console/terminal

    if config.console_print:
        print("-------------------------------------------------------------------------------------------------------")
        print("Output table printing is turned on in the config.py file")
        print("-----Data-----")

        main.print_full(data_fmi)

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

    time3 = time.time()

    # this line saves the results as a csv file
    if config.save_csv:
        print("-------------------------------------------------------------------------------------------------------")
        print("Output table csv exporting is turned on in the config.py file")
        filename = config.save_directory+ config.site_name + str(datetime.date.today()) + ".csv"
        data_fmi.to_csv(filename,float_format='%.2f')
        print("Saved csv as: " + filename)
        print("-------------------------------------------------------------------------------------------------------")

    time4 = time.time()



    plotter.plot_fmi_pvlib_mono(data_fmi, data_pvlib)

    time5 = time.time()

    print("Total time " + str(round((time5 - time0), 3)))
    print("Time fmi " + str(round((time1 - time0), 3)))
    print("Time pvlib " + str(round((time2 - time1), 3)))
    print("Time plotting " + str(round((time5 - time4), 3)))

#__timed_combined_processing_of_data()




def __debug_measure_function_speeds(day_range = 3, data_fmi = None):

    """
    Stats for 10 000 days with 1 hour temp resolution, meaning 240 000 measurements
    #---step 2 irradiance projection 2.721 seconds ---
    #---step 3 radiation absorption modeling 0.92 seconds ---
    #---step 4 adding reflection corrected poa 0.001 seconds ---
    #---step 4.1 estimating wind 0.001 seconds ---
    #---step 5 estimating panel temp 1.421 seconds ---
    #---step 6 estimating power output 1.662 seconds ---
    #---step 7 removing nans 0.012 seconds ---
    #---total time 6.738 seconds ---

    On average, about 35 000 measurements processed through the whole pipeline per second.

    """

    # date for simulation:
    today = datetime.datetime(2024, 6, 12) #datetime.date.today()
    date_start = datetime.datetime(today.year, today.month, today.day)

    data_pvlib = solar_irradiance_estimator.get_solar_irradiance(date_start, day_count=day_range, model="pvlib")

    time_1 = time.time()


    # step 2. project irradiance components to plane of array:
    # this can do about transpose about 10 000 measurements in 0.115 seconds. No further optimization needed
    data_pvlib = helpers.irradiance_transpositions.irradiance_df_to_poa_df(data_pvlib)

    time_2 = time.time()

    # step 3. simulate how much of irradiance components is absorbed:
    # this does 10k in 23 seconds, optimize
    data_pvlib = helpers.reflection_estimator.add_reflection_corrected_poa_components_to_df(data_pvlib)

    time_3 = time.time()

    # step 4. compute sum of reflection-corrected components:
    # 10k in 24 seconds, optimize
    data_pvlib = helpers.reflection_estimator.add_reflection_corrected_poa_to_df(data_pvlib)

    #print_full(data_pvlib)
    time_4 = time.time()

    # step 4.1. adding wind and temperature to dataframe
    # 10k in less than 0.01 seconds, no need to optimize
    if data_fmi is not None:
    # getting data from fmi dataframe if one was given
        data_pvlib = panel_temperature_estimator.add_wind_and_temp_to_df1_from_df2(data_pvlib, data_fmi)
    else:
    # using dummy values if no df was given
        data_pvlib = helpers.panel_temperature_estimator.add_dummy_wind_and_temp(data_pvlib, config.wind_speed,
                                                                                 config.air_temp)

    time_5 = time.time()

    # step 5. estimate panel temperature based on wind speed, air temperature and absorbed radiation
    # 10k in 0.06 seconds, no need to optimize
    data_pvlib = helpers.panel_temperature_estimator.add_estimated_panel_temperature(data_pvlib)


    time_6 = time.time()

    # step 6. estimate power output
    # 10k in 0.07 seconds, no need to optimize
    data_pvlib = helpers.output_estimator.add_output_to_df(data_pvlib)


    time_7 = time.time()

    data_pvlib = data_pvlib.dropna()
    # no need to optimize

    time_8 = time.time()

    print("#---step 2 irradiance projection %s seconds ---" % round((time_2 - time_1),3))
    print("#---step 3 radiation absorption modeling %s seconds ---" % round((time_3 - time_2),3))
    print("#---step 4 adding reflection corrected poa %s seconds ---" % round((time_4 - time_3),3))
    print("#---step 4.1 estimating wind %s seconds ---" % round((time_5 - time_4),3))
    print("#---step 5 estimating panel temp %s seconds ---" % round((time_6 - time_5),3))
    print("#---step 6 estimating power output %s seconds ---" % round((time_7 - time_6),3))
    print("#---step 7 removing nans %s seconds ---" % round((time_8 - time_7),3)) #
    print("#---total time %s seconds ---" % round((time_8 - time_1), 3))

    print(data_pvlib)


    return data_pvlib


__debug_measure_function_speeds(1)

def __process_irradiance_data(meps_data: pandas.DataFrame):
    """
    Processing function for time, dni, dhi, ghi -dataframes
    Generates dataframe with output-variable
    If input does not contain T and wind values, dummies will be added
    """

    # step 2. project irradiance components to plane of array:
    data = helpers.irradiance_transpositions.irradiance_df_to_poa_df(meps_data)

    # step 3. simulate how much of irradiance components is absorbed:
    data = helpers.reflection_estimator.add_reflection_corrected_poa_components_to_df(data)

    # step 4. compute sum of reflection-corrected components:
    data = helpers.reflection_estimator.add_reflection_corrected_poa_to_df(data)

    # step 4.1. add dummy wind and air temp data
    if "T" not in meps_data.columns or "wind" not in meps_data.columns:
        data = helpers.panel_temperature_estimator.add_dummy_wind_and_temp(data, config.wind_speed, config.air_temp)

    # step 5. estimate panel temperature based on wind speed, air temperature and absorbed radiation
    data = helpers.panel_temperature_estimator.add_estimated_panel_temperature(data)

    # step 6. estimate power output
    data = helpers.output_estimator.add_output_to_df(data)

    return data


