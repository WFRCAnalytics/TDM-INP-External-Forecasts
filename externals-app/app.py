# app.py
import pandas as pd
import folium
from shiny import App, ui, render, reactive
import plotly.io as pio
import plotly.graph_objects as go
import numpy as np

# === Data loading ===
externals_df          = pd.read_csv("data/externals.csv")
historic_df           = pd.read_csv("data/historic.csv")
linear_forecasts_df   = pd.read_csv("data/linear-forecasts.csv")
forecasts_df          = pd.read_csv("data/forecasts.csv")
forecasts_previous_df = pd.read_csv("data/forecasts-previous.csv")


# Create choices as a dictionary: {externalid: "Ext #externalid - name"}
external_choices = {
    str(row['externalid']): f"Ext #{row['externalid']} - {row['name']}"
    for _, row in externals_df.sort_values('externalid').iterrows()
}

# === UI ===
app_ui = ui.page_fluid(
    ui.tags.style("""
        body, label, input, select, button, div {
            font-size: 16px !important;
        }
    """),
    ui.panel_title("Wasatch Front TDM Externals Forecast Viewer"),
    ui.layout_columns(
        ui.panel_well(  # Optional for visual grouping
            ui.input_select(
                "externalid",
                "Choose External:",
                choices=external_choices,
                selected=list(external_choices.keys())[0]
            ),
            ui.output_ui("forecast_plot")
        ),
        ui.output_ui("map_container"),
        col_widths=[8, 4]
    )
)

# === Server ===
def server(input, output, session):
    @reactive.Calc
    def selected_externalid():
        return int(input.externalid())

    @render.ui
    def forecast_plot():
        externalid = selected_externalid()

        # Filter datasets
        filtered_historic_df = historic_df[historic_df['externalid'] == externalid]
        filtered_forecasts_df = forecasts_df[forecasts_df['externalid'] == externalid]
        filtered_forecasts_previous_df = forecasts_previous_df[forecasts_previous_df['externalid'] == externalid]
        filtered_linear_forecasts_df = linear_forecasts_df[linear_forecasts_df['externalid'] == externalid]

        fig = go.Figure()
        
        # Add linear forecast line
        fig.add_trace(go.Scatter(
            x=filtered_linear_forecasts_df['year'],
            y=filtered_linear_forecasts_df['linear_forecast'],
            mode='lines+markers',
            name='Historic Linear Extrapolation',
            line=dict(color='lightblue'),
            marker=dict(size=20, symbol='circle'),
            legendrank=4
        ))

        # Add Historic data
        fig.add_scatter(
            x=filtered_historic_df['year'],
            y=filtered_historic_df['AADT'],
            mode='markers',
            name='Historic AADT',
            marker=dict(color='darkgrey', size=10),
            legendrank=2
        )

        # Add Forecast
        fig.add_scatter(
            x=filtered_forecasts_df['year'],
            y=filtered_forecasts_df['final_forecast'],
            mode='markers',
            name='RTP 2027 Forecast (for Review)',
            marker=dict(color='red', size=15),
            legendrank=0
        )

        # Extract data
        x = filtered_forecasts_df['year']
        y = filtered_forecasts_df['final_forecast']

        # Fit a linear regression line
        coeffs = np.polyfit(x, y, deg=1)  # Linear fit (degree 1)
        fitted_line = np.poly1d(coeffs)

        # Generate fitted y-values
        y_fit = fitted_line(x)

        # Add fitted line
        fig.add_scatter(
            x=x, y=y_fit, mode='lines',
            line=dict(color='red', dash='dash'),  # Optional: dashed line for contrast
            name='RTP 2027 Forecast Linear Fit',
            legendrank=3
        )

        # Add Previous Forecast
        fig.add_scatter(
            x=filtered_forecasts_previous_df['year'],
            y=filtered_forecasts_previous_df['previous_forecast'],
            mode='markers',
            name='RTP 2023 Forecast',
            marker=dict(color='orange', size=10),
            legendrank=1
        )

        # Set axis ranges and layout
        # Determine maximum y-value across all series
        y_vals = pd.concat([
            filtered_linear_forecasts_df['linear_forecast'],
            filtered_historic_df['AADT'],
            filtered_forecasts_df['final_forecast'],
            filtered_forecasts_previous_df['previous_forecast']
        ])

        y_max = y_vals.max()

        fig.update_layout(
            title=None,  # remove title entirely
            margin=dict(t=30, b=40, l=40, r=20),  # tight layout: top, bottom, left, right
            yaxis=dict(title="Average Annual Daily Traffic (AADT)", range=[0, y_max * 1.1]),  # Ensure bottom is 0, top padded
            xaxis=dict(range=[1980, 2062])
        )

        fig_html = pio.to_html(fig, full_html=False)
        return ui.HTML(fig_html)


    @render.ui
    def map_container():
        externalid = selected_externalid()

        filtered_externals_df = externals_df[externals_df['externalid'] == externalid]

        # Extract lat/lon
        lat, lon = filtered_externals_df.iloc[0]['lat'], filtered_externals_df.iloc[0]['lon']

        # Create folium map
        fmap = folium.Map(location=[lat, lon], zoom_start=11)
        folium.Marker([lat, lon], tooltip=str(externalid)).add_to(fmap)

        # Use folium's built-in HTML renderer
        return ui.HTML(fmap._repr_html_())


# === App ===
app = App(app_ui, server)