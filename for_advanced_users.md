___
# Advanced usage
The code has been commented and structured so that it should be easy to modify as needed. This file contains some information
on how the program actually works. See also the code files for additional documentation.
___

## Terminology    
* Irradiance: Solar radiation per m², measured in watts.
* DNI: Direct Normal Irradiance, direct sunlight reaching the point of interest without being scattered or absorbed in the atmopshere. Imagine the irradiance at the bottom of a long tube pointing towards the Sun.
* DHI: Diffuse Horizontal Irradiance, indirect sunlight scattered from the atmosphere. Complement of DNI. Imagine system which blocks direct sunlight from reaching the point of interest, but does not block any irradiance from other segments of the sky.
* GHI: Global Horizontal Irradiance. Sum of DNI (projected to a horizontal surface) and DHI.
* Irradiance transpositions: Irradiance types have to be projected to the panel surface. Functions for each irradiance type are different.
* Reflection loss estimation: Solar panel surfaces reflect a proportion of solar irradiance away from solar panels. These reflective losses depend on the angle at which irradiance reaches the panel surface. Irradiance - Reflected irradiance = Absorbed irradiance.
* Temperature estimation: Solar panel efficiency is influenced by panel temperatures. Panel temperatures can be estimated based on absorbed radiation and assumed air temperature.
* AOI/Angle of incidence: Angle between solar panel normal and direct sunlight.

## PV model flowchart
![Solar PV model flowchart](documentation_pictures/simulation_flowchart.png)

The PV model used by this program works according to the figure above. In theoretical clear sky PV generation simulations,
the DNI, DHI, GHI table comes from PVlib simulations whereas in weather model based simulations this same table is fetched from FMI Open Data.

After the DNI, DHI, GHI-tables are ready, both theoretical and weather model based DNI,
DHI and GHI are processed through the same pipeline.

## Performance
The processing pipeline was optimized in the November 2024 update. As tested on a ryzen 5 5600x desktop, the
system is capable of using pvlib to generate and process 35,000 triplets of DNI, DHI and GHI to the system output per
second. This means that in 1 second, the application should be able to generate and process 24 days of 1 minute resolution data using PVlib.

At this point, it is unlikely that the program speed can be increased meaningfully as most of the time is spent in
waiting for FMI open data server responses and generating the plot with matplotlib. Performance increases would be possible
if multithreading was added, but the benefits would not insignificant.

Runtimes for combined_processing_of_data() in main.py and saving a plot as a png on the same test machine:
- Total runtime 480ms(0.48 seconds).
- FMI Data processing 128ms.
  - Time retrieving data from fmi open data 92ms with a ping of 1ms.
  - Formatting fmi open data before pipeline 11ms.
  - Processing fmi open data with the PV model pipeline 25ms.
- Time generating and using PV model pipeline 27ms.
- Time spent plotting 320ms.

Times are approximates and may vary from run to run and system to system.





## Code files and flowchart steps

- DNI, DHI, GHI simulation simulation: solar_irradiance_estimator.py, _meps_data_loader.py , meps_data_parser.py
- Projecting DNI, DHI and GHI: irradiance_transpositions.py
- Reflection estimation: reflection_estimator.py
- Temperature estimation: panel_temperature_estimator.py
- Output estimation: output_estimator.py
- Testing functions

<!-- 


## Program structure
* astronomical_calculations.py
    * Used for calculating sunlight angles, required for irradiance transpositions.
* config.py
    * Stores installation specific variables such as geolocation, ground albedo, timezone and so on.
* irradiance_transpositions.py
    * Contains functions for projecting the three simulated irradiance components DNI, DHI, GHI to the surface of solar panels.
* main.py
    * Controls the system. Avoid writing complex code here. The file contains samples on how to operate the forecaster.
* panel_temperature_model.py
    * Solar PV module temperature estimation equations. Physically accurate, require ambient temperature, panel elevation from ground and wind speed values.
* plotter.py
    * Functions for plotting visualizations.
* reflection_estimator.py
    * Functions for estimating how much of the irradiance which hits solar panel surfaces is absorbed and not reflected away.
* solar_irradiance_estimator.py
    * Estimates solar irradiance based on given model name. Supports clear sky and weather prediction-based estimates.

**Data Flow:**
1. Use solar_irradiance_estimator.py to generate a dataframe with dni, dhi, and ghi values.
These represent different types of irradiance which is radiated towards solar panels.

2. Use irradiance_transpositions.py to estimate how dni, dhi, and ghi are projected to solar panel surfaces. These surface projected values are stored as dni_poa, dhi_poa, ghi_poa and their sum poa.
3. Use reflection_estimator.py to estimate how much of dni_poa, dhi_poa, ghi_poa is absorbed by solar panels and how much is reflected away. Store the sum as poa_refl_cor.


**Resulting dataframe structure:**

 | time                       |   dni    |    ghi   |    dhi  |   dni_poa  | ghi_poa |  dhi_poa  |   poa  | poa_ref_cor|
|----------------------------|----------|----------|---------|------------|---------|-----------|--------|------------|
| 2023-10-13 00:00:00+03:00  |    0.00  |    0.00 |    0.00  |     0.00   |    0.00  |     0.00   |    0.00    |     0.00|
| 2023-10-13 00:15:00+03:00  |    0.00  |    0.00 |      0.00 |      0.00  |     0.00  |     0.00   |    0.00   |      0.00|
| 2023-10-13 00:30:00+03:00  |    0.00  |    0.00 |      0.00 |      0.00  |     0.00  |     0.00   |    0.00   |      0.00|
| 2023-10-13 00:45:00+03:00  |    0.00  |    0.00 |      0.00 |      0.00  |     0.00  |     0.00   |    0.00   |      0.00|
|  2023-10-13 01:00:00+03:00 |    0.00  |    0.00 |      0.00 |      0.00  |     0.00  |     0.00   |    0.00   |      0.00|

-->





## Code samples
### Pvlib data processing function:
```python
# This function is located in main.py
def get_fmi_data(day_range= 3):
    # date for simulation:
    today = datetime.date.today()
    date_start = datetime.datetime(today.year, today.month, today.day)

    # step 1. simulate irradiance components dni, dhi, ghi:
    data = solar_irradiance_estimator.get_solar_irradiance(date_start, day_count=day_range, model="fmiopen")

    # step 2. project irradiance components to plane of array:
    data = helpers.irradiance_transpositions.irradiance_df_to_poa_df(data)

    # step 3. simulate how much of irradiance components is absorbed:
    data = helpers.reflection_estimator.add_reflection_corrected_poa_components_to_df(data)

    # step 4. compute sum of reflection corrected components:
    data = helpers.reflection_estimator.add_reflection_corrected_poa_to_df(data)

    # step 5. estimate panel temperature based on wind speed, air temperature and absorbed radiation
    data = helpers.panel_temperature_estimator.add_estimated_panel_temperature(data)

    # step 6. estimate power output
    data = helpers.output_estimator.add_output_to_df(data)

    return data
```

### PVlib and FMI Open Data plotting:
```python
# This function is located in main.py
def combined_processing_of_data():
    """
    Uses both pvlib and fmi open to compute solar irradiance for the next 4 days and plots both
    :return:
    """

    # helper functions:
    data_pvlib = get_pvlib_data(4)
    data_fmi = get_fmi_data(4)

    print_full(data_fmi)
    print_full(data_pvlib)
    
    # mono plotting
    plotter.plot_fmi_pvlib_mono(data_fmi, data_pvlib)

```
