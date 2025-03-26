from shiny import App, render, ui, reactive
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np
import re

# Load the data
data_path = Path("params/externals.csv")
df = pd.read_csv(data_path)

# Create label for dropdown in format "externalid, name"
df["label"] = df["externalid"].astype(str) + ": " + df["name"]
unique_options = df[["externalid", "label"]].drop_duplicates()

aadt_df = pd.read_csv('data/Traffic_Volume_Historic_and_Forecast_20250326.csv')

# Load AADT forecast data
aadt_df = pd.read_csv("data/AADTHistory 2023.xlsx - RoundedAADT2023.csv")
segment_link = pd.read_csv("params/externals-forecast-segments.csv")  # Contains 'externalid' and 'segid'

# Melt AADT columns
aadt_year_cols = [col for col in aadt_df.columns if re.match(r"AADT\d{4}$", col)]
aadt_melted = aadt_df.melt(id_vars=["STATION","RouteID","BeginPoint","EndPoint","Section_Length","DESC"], value_vars=aadt_year_cols,
                           var_name="year", value_name="AADT")
aadt_melted["year"] = aadt_melted["year"].str.extract(r"(\d{4})").astype(int)

# Extract first 4 digits of RouteID if present
route_extracted = aadt_melted["RouteID"].str.extract(r"^(\d{4})")
aadt_melted["route"] = route_extracted[0].dropna().astype(int)

# Join with segment link and externals
aadt_merged = aadt_melted.merge(segment_link, on="segid")
aadt_merged = aadt_merged.merge(df, on="externalid")

# Define UI
app_ui = ui.page_fluid(
    ui.h2("Line Series with Trend Lines"),
    ui.input_select("selected_external", "Select External ID:",
                   choices={row.externalid: row.label for _, row in unique_options.iterrows()}),
    ui.output_plot("line_plot", height="500px")
)

# Define server
def server(input, output, session):
    @reactive.Calc
    def filtered_data():
        return aadt_merged[aadt_merged.externalid == input.selected_external()]

    @output
    @render.plot
    def line_plot():
        fdata = filtered_data()

        plt.figure(figsize=(10, 6))

        for sid, group in fdata.groupby("segid"):
            plt.plot(group["year"], group["AADT"], label=f"Segment {sid}")

            # Fit and plot linear trend line
            coeffs = np.polyfit(group["year"], group["AADT"], 1)
            trend = np.poly1d(coeffs)
            plt.plot(group["year"], trend(group["year"]), linestyle='--', alpha=0.5)

        plt.title(f"AADT Forecast for {input.selected_external()} - {fdata['name'].iloc[0]}")
        plt.xlabel("Year")
        plt.ylabel("AADT")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

# Run app
app = App(app_ui, server)