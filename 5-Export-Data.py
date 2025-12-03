#!/usr/bin/env python
# coding: utf-8

# # Set Up Environment

# ## Import Libraries

# In[1]:


import numpy as np
import pandas as pd
import geopandas as gpd
# import pygwalker as pyg

import requests
import io
import os

from scipy import stats
from dotenv import load_dotenv

load_dotenv()


# ## Set Environment Variables

# In[2]:


PROJECT_CRS = "EPSG:3566"


# ## Helper Functions

# In[3]:


def fetch_github(
    url: str, mode: str = "private", token_env_var: str = "GITHUB_TOKEN"
) -> requests.Response:
    """
    Fetch content from GitHub repositories.

    Args:
        url: GitHub raw URL (e.g., https://raw.githubusercontent.com/...)
        mode: "public" for public repos, "private" for private repos requiring authentication
        token_env_var: Name of environment variable containing GitHub token (default: GITHUB_TOKEN)

    Returns:
        requests.Response object

    Raises:
        ValueError: If token is missing for private mode or invalid mode
        requests.HTTPError: If request fails
    """

    # Validate mode
    if mode not in ["public", "private"]:
        raise ValueError(f"mode must be 'public' or 'private', got '{mode}'")

    if mode == "public":
        response = requests.get(url, timeout=30)
    else:
        token = os.getenv(token_env_var)
        if not token:
            raise ValueError(
                f"GitHub token not found in environment variable '{token_env_var}'. "
                f"Check your .env file has: {token_env_var}=your_token_here"
            )

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3.raw",
        }
        response = requests.get(url, headers=headers, timeout=30)

    response.raise_for_status()
    return response


# In[4]:


def fill_linear_regression(series, x_values):
    """
    Used for AADT Back-casting.
    Fills NaN values using linear regression based on existing points in the series.
    """
    mask = series.notna()
    if mask.sum() < 2:
        return series.ffill().bfill()  # Fallback if not enough points

    slope, intercept, _, _, _ = stats.linregress(x_values[mask], series[mask])
    return series.where(series.notna(), slope * x_values + intercept)


# In[5]:


def project_future_volumes(group, value_col, year_col, split_year=2023):
    """
    Used for Truck Volume Projection.
    Regresses on Historic data (Year < split_year) and predicts Future data (Year >= split_year).
    """
    # 1. Identify Historic Data for Training
    hist_mask = (group[year_col] < split_year) & (group[value_col].notna())

    # 2. If insufficient historic data, forward fill the last known value
    if hist_mask.sum() < 2:
        last_known = (
            group.loc[group[year_col] < split_year, value_col].iloc[-1]
            if hist_mask.any()
            else 0
        )
        group.loc[group[year_col] >= split_year, value_col] = last_known
        return group[value_col]

    # 3. Train Regression Model
    x_hist = group.loc[hist_mask, year_col].values
    y_hist = group.loc[hist_mask, value_col].values
    slope, intercept, _, _, _ = stats.linregress(x_hist, y_hist)

    # 4. Predict Future
    future_mask = group[year_col] >= split_year
    x_future = group.loc[future_mask, year_col].values
    predicted = slope * x_future + intercept

    # Apply prediction (ensure no negative volumes)
    group.loc[future_mask, value_col] = np.maximum(predicted, 0)

    return group[value_col]


# # Input Data

# ## Preprocessed Forecast Results (Future Points: 2027, 2035...)

# In[6]:


forecast_results = pd.read_csv("results/final_forecast_df.csv")
forecast_results[["externalid", "year", "final_forecast"]]


# ## Traffic Factors (Master Segments)

# In[7]:


gdf_master_segments = gpd.read_file(
    "zip://data/updated-traffic-factors/Master_Segs_withFactors_20251120.zip"
).to_crs(PROJECT_CRS)

gdf_master_segments


# ## UDOT AADT & Truck % (Historic from GitHub)

# In[8]:


# Read Processed UDOT AADT Daya directly from GitHub repo
response = fetch_github(
    "https://raw.githubusercontent.com/WFRCAnalytics/DATA-UDOT-AADT-Processing/refs/heads/main/_output/udot_aadt_trkpct_data.csv",
    mode="private",
)

df_aadt_udot = pd.read_csv(io.StringIO(response.text))

df_aadt_udot


# ## External-Segment Link

# In[9]:


external_segment_link = pd.read_csv("params/externals-segments-link.csv")
external_segment_link


# ## Archive / Legacy Data (The Fallback Source)

# In[10]:


df_external_year_archive = pd.read_csv(r"archive/v920/external_year_vol.csv")

df_external_year_archive


# # Prepare Data

# ## Step 1: Initialize Final Dataframe Structure

# In[11]:


# Step 1: Initiate dataframe with the id, and year columns
df_external_year = (
    pd.MultiIndex.from_product(
        [external_segment_link["externalid"].unique(), range(1981, 2061)],
        names=["WF_Ext", "Year"],
    )
    .to_frame(index=False)
    .reset_index(drop=True)
)

# Create Index String
df_external_year[";Idx_WF"] = df_external_year["WF_Ext"].astype(str) + df_external_year[
    "Year"
].astype(str)

# Map Metadata
df_external_year["segid"] = df_external_year["WF_Ext"].map(
    external_segment_link.set_index("externalid")["segid"]
)
df_external_year["route"] = df_external_year["segid"].str.split("_").str[0] + "PM"
df_external_year["milepost"] = pd.to_numeric(
    df_external_year["segid"].str.split("_").str[1], errors="coerce"
)

# Map Station Name
df_external_year["Ext_Name"] = df_external_year["WF_Ext"].map(
    forecast_results[["externalid", "external"]]
    .drop_duplicates()
    .set_index("externalid")["external"]
)

df_external_year


# ## Step 2: AWDT Factors (With Fallback)

# In[12]:


# Primary: From Master Segments
df_external_year["AWDT_FAC"] = df_external_year["segid"].map(
    gdf_master_segments.set_index("SEGID")["FAC_WDAVG"]
)

# Fallback: From Archive (Match WF_Ext + Year)
# We set the index of both to map efficiently
archive_fac_map = df_external_year_archive.set_index(["WF_Ext", "Year"])["AWDT_FAC"]
df_external_year = df_external_year.set_index(["WF_Ext", "Year"])
df_external_year["AWDT_FAC"] = df_external_year["AWDT_FAC"].fillna(archive_fac_map)
df_external_year = df_external_year.reset_index()

# Clean up: Replace 0s with 1 (or NA) to prevent math errors, assuming 1 if missing
df_external_year["AWDT_FAC"] = df_external_year["AWDT_FAC"].replace(0, 1).fillna(1)

df_external_year


# ## Step 3: Historic Data Integration (1981 - 2022)

# In[13]:


# 1. Merge UDOT Data based on Year and Route
#    (Matches all available years, including 2023 and 2024)
udot_subset = df_aadt_udot[
    ["YEAR", "RouteID", "BeginPoint", "AADT", "SUTRK", "CUTRK"]
].copy()

# Perform merge
df_merged = df_external_year.merge(
    udot_subset, left_on=["Year", "route"], right_on=["YEAR", "RouteID"], how="left"
)

# 2. Filter for nearest milepost (distance calc)
df_merged["distance"] = (df_merged["BeginPoint"] - df_merged["milepost"]).abs()
df_historic_matches = (
    df_merged.sort_values("distance").groupby([";Idx_WF"]).first().reset_index()
)

# 3. Update the main df with these matches
cols_to_update = {"AADT": "AADT_Historic", "SUTRK": "PctTrk_SU", "CUTRK": "PctTrk_MU"}
for src, dest in cols_to_update.items():
    df_external_year[dest] = df_external_year[";Idx_WF"].map(
        df_historic_matches.set_index(";Idx_WF")[src]
    )

# 4. Fallback: Fill Historic Gaps from Archive

# Allow fallback/filling up to 2024 to ensure AADT_Historic is complete
# even though we only use it up to 2022 for the final calculation.
mask_historic_availability = df_external_year["Year"] <= 2024

# Define the columns we want to fallback for
fallback_cols = ["AADT", "PctTrk_SU", "PctTrk_MU"]
target_cols = ["AADT_Historic", "PctTrk_SU", "PctTrk_MU"]

# Create an indexer for the historic period
mask_historic_period = df_external_year["Year"] < 2023

# Loop through and apply fallback for each column
for archive_col, target_col in zip(fallback_cols, target_cols):
    # 1. Create the Map from Archive
    # Note: Ensure the column name in archive matches 'archive_col'
    archive_map = df_external_year_archive.set_index(["WF_Ext", "Year"])[archive_col]

    # 2. Create aligned Series for the main dataframe
    fallback_series = pd.Series(
        df_external_year.set_index(["WF_Ext", "Year"]).index.map(archive_map),
        index=df_external_year.index,
    )

    # 3. Fill NaNs in the target column, strictly for Historic years
    df_external_year.loc[mask_historic_period, target_col] = df_external_year.loc[
        mask_historic_period, target_col
    ].fillna(fallback_series)

df_external_year


# # Step 4: Forecast Data & AADT Hybridization

# In[14]:


# Map Forecast Results
df_external_year["AADT_Forecast"] = df_external_year.set_index(
    ["WF_Ext", "Year"]
).index.map(forecast_results.set_index(["externalid", "year"])["final_forecast"])

# Extrapolate/Back-cast Forecast (Fill 2023-2026 using trend from 2027+)
# We treat 2023 onwards as the "Forecast Period" for the sake of the regression
forecast_mask = df_external_year["Year"] >= 2023

df_external_year.loc[forecast_mask, "AADT_Forecast"] = (
    df_external_year[forecast_mask]
    .groupby("WF_Ext", group_keys=False)["AADT_Forecast"]
    .apply(
        lambda g: fill_linear_regression(
            g.astype(float), df_external_year.loc[g.index, "Year"]
        )
    )
)

# Create Combined AADT Column (The "Final" Column)
# Logic: Use Historic if < 2023, else use Forecast
df_external_year["AADT"] = np.where(
    df_external_year["Year"] < 2023,
    df_external_year["AADT_Historic"],
    df_external_year["AADT_Forecast"],
)

# Ensure data types (Int64 allows NaNs)
df_external_year["AADT"] = (
    pd.to_numeric(df_external_year["AADT"], errors="coerce").round().astype("Int64")
)

df_external_year


# ## Step 5: Truck Volume Projections

# In[15]:


# A. Calculate Base Historic Volumes (Rows < 2023)
# We fill percentages with 0 temporarily to avoid NaN * Number errors,
# but keep the result as NaN if AADT was NaN
df_external_year["TRUCK_SU"] = (
    df_external_year["AADT"] * df_external_year["PctTrk_SU"].fillna(0)
).where(df_external_year["PctTrk_SU"].notna())

df_external_year["TRUCK_MU"] = (
    df_external_year["AADT"] * df_external_year["PctTrk_MU"].fillna(0)
).where(df_external_year["PctTrk_MU"].notna())

# B. Project Future Volumes (Rows >= 2023)
# We use the helper function to regress historic volumes and predict future
df_external_year["TRUCK_SU"] = df_external_year.groupby(
    "WF_Ext", group_keys=False
).apply(
    lambda g: project_future_volumes(g, "TRUCK_SU", "Year", split_year=2023),
    include_groups=False,
)

df_external_year["TRUCK_MU"] = df_external_year.groupby(
    "WF_Ext", group_keys=False
).apply(
    lambda g: project_future_volumes(g, "TRUCK_MU", "Year", split_year=2023),
    include_groups=False,
)

# Round Truck Volumes
df_external_year["TRUCK_SU"] = (
    pd.to_numeric(df_external_year["TRUCK_SU"]).round().astype("Int64")
)

df_external_year["TRUCK_MU"] = (
    pd.to_numeric(df_external_year["TRUCK_MU"]).round().astype("Int64")
)

# C. Back-Calculate Future Percentages
df_external_year["PctTrk_SU"] = df_external_year["TRUCK_SU"] / df_external_year["AADT"]
df_external_year["PctTrk_MU"] = df_external_year["TRUCK_MU"] / df_external_year["AADT"]

df_external_year


# ## Step 6: Passenger & Weekly Counts

# In[16]:


# Passenger
df_external_year["PASSENGER"] = (
    (
        df_external_year["AADT"]
        - (
            df_external_year["TRUCK_SU"].fillna(0)
            + df_external_year["TRUCK_MU"].fillna(0)
        )
    )
    .round()
    .astype("Int64")
)

# Weekly Conversions (Apply Factors)
df_external_year["AWDT"] = (
    (df_external_year["AADT"] * df_external_year["AWDT_FAC"]).round().astype("Int64")
)
df_external_year["PASS_VOL"] = (
    (df_external_year["PASSENGER"] * df_external_year["AWDT_FAC"])
    .round()
    .astype("Int64")
)
df_external_year["TRUCK_MD"] = (
    (df_external_year["TRUCK_SU"] * df_external_year["AWDT_FAC"])
    .round()
    .astype("Int64")
)
df_external_year["TRUCK_HV"] = (
    (df_external_year["TRUCK_MU"] * df_external_year["AWDT_FAC"])
    .round()
    .astype("Int64")
)

df_external_year


# ## Step 7: Vintage Labeling

# In[17]:


df_external_year["Vintage"] = np.select(
    [df_external_year["Year"] < 2023, df_external_year["Year"] >= 2023],
    ["Historic", "Forecast"],
    default="Unknown",
)

df_external_year


# # Visualize

# In[18]:


import pandas as pd
import plotly.graph_objects as go
import ipywidgets as widgets
from ipywidgets import interact

# ==========================================
# 1. PREPARE DATA
# ==========================================

# Filter Data: Year >= 2010
df_viz = df_external_year[df_external_year["Year"] >= 2010].copy()

# ==========================================
# 2. DEFINE PLOTTING FUNCTION
# ==========================================


def plot_station(station_name):
    # Filter for the selected station
    df_s = df_viz[df_viz["Ext_Name"] == station_name].sort_values("Year")

    if df_s.empty:
        print("No data found for this station.")
        return

    # --- Strict Vintage Slicing ---
    # Rely purely on the 'Vintage' column labels
    df_hist = df_s[df_s["Vintage"] == "Historic"]
    df_curr = df_s[df_s["Vintage"] == "Current"]
    df_fore = df_s[df_s["Vintage"] == "Forecast"]

    # --- Connectivity Logic ---
    # Manually attach the last point of the previous segment to the start of the next
    # to ensure visual continuity without recalculating year boundaries.

    # 1. Connect Historic -> Current
    if not df_hist.empty and not df_curr.empty:
        # Prepend last Historic row to Current
        df_curr = pd.concat([df_hist.iloc[[-1]], df_curr])

    # 2. Connect Current -> Forecast
    if not df_fore.empty:
        if not df_curr.empty:
            # Prepend last Current row to Forecast
            df_fore = pd.concat([df_curr.iloc[[-1]], df_fore])
        elif not df_hist.empty:
            # Direct Jump: Historic -> Forecast (if Current is missing)
            df_fore = pd.concat([df_hist.iloc[[-1]], df_fore])

    # --- Plotting ---
    fig = go.Figure()

    # TRACE ORDER: Forecast -> Current -> Historic

    # 1. Forecast (Dotted Line, Hollow Dots)
    fig.add_trace(
        go.Scatter(
            x=df_fore["Year"],
            y=df_fore["AADT"],
            mode="lines+markers",
            name="Forecast",
            line=dict(color="#D32F2F", width=2.5, dash="dot"),
            marker=dict(color="white", size=7, line=dict(color="#D32F2F", width=2)),
            hovertemplate="<b>%{x}</b>: %{y:,} (Forecast)<extra></extra>",
        )
    )

    # 2. Current (Dotted Line, Solid Dots)
    fig.add_trace(
        go.Scatter(
            x=df_curr["Year"],
            y=df_curr["AADT"],
            mode="lines+markers",
            name="Current",
            line=dict(color="#D32F2F", width=2.5, dash="dot"),
            marker=dict(color="#D32F2F", size=7, line=dict(color="#D32F2F", width=2)),
            hovertemplate="<b>%{x}</b>: %{y:,} (Current)<extra></extra>",
        )
    )

    # 3. Historic (Solid Line, Solid Dots)
    fig.add_trace(
        go.Scatter(
            x=df_hist["Year"],
            y=df_hist["AADT"],
            mode="lines+markers",
            name="Historic",
            line=dict(color="#D32F2F", width=2.5, dash="solid"),
            marker=dict(color="#D32F2F", size=7, line=dict(color="#D32F2F", width=2)),
            hovertemplate="<b>%{x}</b>: %{y:,} (Historic)<extra></extra>",
        )
    )

    # Layout
    fig.update_layout(
        title=dict(text=f"AADT Trend: <b>{station_name}</b>", font=dict(size=18)),
        xaxis=dict(
            title="Year", dtick=5, showgrid=True, gridcolor="#eee", linecolor="#333"
        ),
        yaxis=dict(
            title="AADT",
            tickformat=",",
            showgrid=True,
            gridcolor="#eee",
            linecolor="#333",
            rangemode="tozero",  # Y-axis starts at 0
        ),
        plot_bgcolor="white",
        height=500,
        legend=dict(orientation="h", y=1.05, x=1, xanchor="right"),
        margin=dict(l=40, r=40, t=80, b=40),
    )

    fig.show()


# ==========================================
# 3. CREATE WIDGET
# ==========================================

station_options = sorted(df_viz["Ext_Name"].dropna().unique())

interact(
    plot_station,
    station_name=widgets.Dropdown(
        options=station_options,
        description="Station:",
        style={"description_width": "initial"},
        layout={"width": "500px"},
    ),
)


# # Export Final Results

# In[19]:


os.makedirs("results", exist_ok=True)

(
    df_external_year[
        # 1. Filter columns using the predefined list
        [
            ";Idx_WF",
            "WF_Ext",
            "Year",
            "AWDT",
            "PASS_VOL",
            "TRUCK_MD",
            "TRUCK_HV",
            "AWDT_FAC",
            "AADT",
            "PASSENGER",
            "TRUCK_SU",
            "TRUCK_MU",
            "PctTrk_SU",
            "PctTrk_MU",
        ]
    ][
        # 2. Filter rows using the boolean mask (Year >= 2010)
        df_external_year["Year"] >= 2010
    ]
    # 3. Export to CSV
    .to_csv("results/external_year_vol.csv", index=False)
)

