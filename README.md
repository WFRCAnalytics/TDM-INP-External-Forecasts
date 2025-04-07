# TDM-INP-External-Forecasts

This repo contains the volume forecasts for externals for the Wasatch Front Travel Demand Model. The works is contained in five jupyter notebooks.

**1-Get-Historic-AAADT.ipynb:** The Average Annual Daily Traffic (AADT) historic data from the Utah Department of Transportation is matched to each external.

**2-Prepare-Previous-Forecasts.ipynb:** Forecasts from previous model versions are gathered and processed to inform forecasting.

**3-Prepare-Linear-Forecasts.ipynb:** Linear forecasts are created off an extrapolated linear least-square regression fit of the historic AADT. These trend lines are created for a user-defined set of year ranges, eg. 2011-2023 linear forecast.

**4-Finalize-Forecasts.ipynb:** Using a series of charts, forecaster determines the linear forecasts to use for each external, and then defines further manual adjustments as needed.

**5-Prepare-TDM-Inputs.ipynb.** The inputs for the extnerals for the TDM are generated.
