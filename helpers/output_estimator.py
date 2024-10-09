"""
This file contains functions for estimating PV system output using Huld et. al 2010 PV output model
Required input is a dataframe with columns which contain absorbed radiation and panel temperature.
These columns are named "poa_ref_cor"(plane of array irradiance with reflection corrections) and
"module_temp" for PV module temperature.

Author: TimoSalola (Timo Salola).
"""


import math
import pandas
import pandas as pd
import numpy

import config

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

def add_output_to_df(df: pandas.DataFrame)-> pandas.DataFrame:
    """
    Checker function for testing if required parameters exist in DF, if they do, add output to DF.
    :param df: Pandas dataframe with required columns for absorbed irradiance and panel temperature.
    :return: Input DF with PV system output column.
    """

    # new PV output models can be added here if needed.


    if "poa_ref_cor" not in df.columns:
        print("column poa_ref_cor not found in dataframe, output can not be simulated")
    if "module_temp" not in df.columns:
        print("module temperature variable \"module_temp\" not found in dataframe")


    # filtering negative values out
    df['poa_ref_cor'] = df['poa_ref_cor'].apply(lambda x: 0 if x < 0 else x)
    # estimating output
    #df["output"] =   __estimate_output(df["poa_ref_cor"], df["module_temp"])
    # ^ raises errors if first input absorbed_radiation is 0.0

    # this line makes ure the outpu estimation is not called when per w² radiation is below 0.1W. If the radiation is
    # this low, the system would not produce any power and values of 0.0 cause issues as the output model contains
    # logarithms
    df['output'] = df.apply(
        lambda row: 0.0 if row['poa_ref_cor'] < 0.1 else __estimate_output(row['poa_ref_cor'], row['module_temp']),
        axis=1
    )

    # filling nans
    df['output'] = df['output'].fillna(0.0)

    return df


def __estimate_output(absorbed_radiation: float, panel_temp: float)-> float:

    """
    Huld 2010 model
    T.~Huld, R.~Gottschalg, H.~G. Beyer, and M.~Topič,
    Mapping the performance of PV modules, effects of module type and
    data averaging, Solar Energy, 84 324--338 (2010).

    The Huld 2010 model may not perform very well at low irradiances. Solar panel efficiency tends to decrease
    when irradiance per m² of panel surface is less than 300W. This is taken into account by the Huld model, but
    depending on panel types and other factors, the Huld model may actually suggest a negative efficiency.
    During testing, this occurred at m² irradiances of less than 5W but this is temperature dependant.

    As finding reliable information on PV panel output at lower than 100W/m² irradiances proved to be challenging,
    it may very well be possible that either efficiency varies vastly depending on the panel type or efficiency
    actually goes to zero.

    A minimum efficiency of 50% has been set. Adjust [min_efficiency] if this is not to your liking. This will not
    affect the performance of the model a lot, but it will eliminate negative output estimates and thus a limit.

    :param absorbed_radiation: Solar irradiance absorbed by m² of solar panel surface.
    :param panel_temp: Estimated solar panel temperature.
    :return: Estimated system output in watts.
    """

    min_efficiency = 0.5

    # huld 2010 constants
    k1 = -0.017162
    k2 = -0.040289
    k3 = -0.004681
    k4 = 0.000148
    k5 = 0.000169
    k6 = 0.000005

    # hud et al equation:

    # main equation:
    # output = rated_power*nrad*efficiency

    # Helpers:
    # nrad = absorbed_radiation/1000
    # Tdiff = module_temp-25C
    # efficiency = 1+ k1*ln(nrad)
    # + k2*ln(nrad)²
    # + Tdiff*(k3+k4*ln(nrad) + k5*ln(nrad)²)
    # + k6*Tdiff²

    #print(absorbed_radiation)

    nrad = absorbed_radiation / 1000.0
    Tdiff = panel_temp - 25
    rated_power = config.rated_power * 1000.0
    base = 1

    part_k1 = k1 * numpy.log(nrad)
    part_k2 = k2*(numpy.log(nrad)**2)
    part_k3k4k5 = Tdiff*(k3+k4*numpy.log(nrad) + k5*(numpy.log(nrad)**2))
    # T*(-0.004681+0.000148*log(x) + 0.000169*log(x)²)
    part_k6 = k6*(Tdiff**2)

    efficiency = base + part_k1+ part_k2 + part_k3k4k5 + part_k6
    efficiency = numpy.maximum(efficiency, min_efficiency)
    # huld efficiencies can be negative, fixing that here

    #print(absorbed_radiation)
    #print("efficiency:" + str(efficiency))

    output = rated_power*nrad*efficiency



    return output

