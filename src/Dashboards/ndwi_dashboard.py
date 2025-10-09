import streamlit as st
import geopandas as gpd
import pandas as pd
import json
import folium
import calendar
import plotly.express as px
from streamlit_folium import st_folium
from data_loader import load_aoi_data


# --------------------------
# NDWI Rate Change
# --------------------------
def show_ndwi_trend(df):
    """
    Displays the NDWI trend as an area chart in a Streamlit metric.
    The delta shows the change between the last two measurements.

    Parameters:
    - df: DataFrame with columns 'date' and 'NDWI_mean'
    """
    df = df.sort_values("date")
    ndwi_mean = df["NDWI_mean"].values

    if len(ndwi_mean) < 2:
        st.metric(
            "NDWI Trend",
            round(ndwi_mean[-1], 3) if len(ndwi_mean) > 0 else "N/A",
            "N/A",
            chart_data=ndwi_mean,
            chart_type="line",
            border=True,
        )
        return

    recent_delta = round(ndwi_mean[-1] - ndwi_mean[-2], 3)
    chart_data = ndwi_mean

    st.metric(
        "NDWI Trend",
        round(ndwi_mean[-1], 3),
        recent_delta,
        chart_data=chart_data,
        chart_type="line",
        border=True,
    )

    st.metric(
        "NDWI Trend",
        round(ndwi_mean[-1], 3),
        recent_delta,
        chart_data=chart_data,
        chart_type="area",
        border=True,
    )


# --------------------------
# NDWI Seasonal Heatmap
# --------------------------
def plot_ndwi_heatmap_plotly(df: pd.DataFrame, width: int = 700, height: int = 370):
    """Plot interactive NDWI seasonal heatmap for years using Plotly."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    if "month_num" not in df.columns:
        df["month_num"] = df["date"].dt.month

    heatmap_df = df.pivot_table(index="year", columns="month_num", values="NDWI_mean")
    heatmap_df = heatmap_df.reindex(columns=range(1, 13))

    month_labels = [calendar.month_abbr[i] for i in range(1, 13)]

    fig = px.imshow(
        heatmap_df,
        labels=dict(x="Month", y="Year", color="NDWI Mean"),
        x=month_labels,
        color_continuous_scale="Blues",
        text_auto=".2f",
        aspect="auto",
        width=width,
        height=height,
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Year",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=40, r=40, t=60, b=40),
    )
    st.write(":blue[NDWI Seasonal Heatmap]")
    st.plotly_chart(fig, use_container_width=True)


# --------------------------
# Show Data Table
# --------------------------
def show_data(df: pd.DataFrame, width: int = 700, height: int = 450):
    show_cols = ["date", "NDWI_mean", "NDWI_std"]
    st.write(":blue[NDWI Data]")
    st.dataframe(df[show_cols], width=width, height=height)


# --------------------------
# AOI Map
# --------------------------
def render_aoi_map(
    aoi_json: dict, width: int = 600, height: int = 440, map_type: str = "standard"
):
    """
    Render AOI map with selectable basemap type.

    Parameters:
    - aoi_json: AOI GeoJSON dictionary
    - width: Map width in pixels
    - height: Map height in pixels
    - map_type: "default" for OpenStreetMap, "satellite" for ESRI Satellite
    """
    gdf = gpd.GeoDataFrame.from_features(aoi_json["features"])
    centroid = gdf.geometry.centroid.iloc[0]

    # Initialize map without tiles
    m = folium.Map(location=[centroid.y, centroid.x], zoom_start=8, tiles=None)

    # Add the selected base layer
    if map_type.lower() == "satellite":
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Tiles © Esri & Maxar",
            name="Satellite",
            overlay=False,
            control=False,
        ).add_to(m)
    else:  # default OpenStreetMap
        folium.TileLayer(
            "OpenStreetMap", name="OSM", overlay=False, control=True
        ).add_to(m)

    # Add AOI polygon
    folium.GeoJson(
        aoi_json,
        name="AOI",
        style_function=lambda x: {
            "color": "#4CAF50",
            "weight": 3,
            "opacity": 0.7,
        },
    ).add_to(m)

    # Layer control to allow switching layers if needed
    folium.LayerControl(collapsed=False).add_to(m)

    # Hide attribution (optional)
    st.markdown(
        """
        <style>
            .leaflet-control-attribution {display:none !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.write(":green[Area of Interest (AOI)]")
    st_folium(m, width=width, height=height)


# --------------------------
# NDWI Line Chart
# --------------------------
def plot_ndwi(df: pd.DataFrame, show_var: bool):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    if show_var:
        fig = px.line(
            df,
            x="date",
            y="NDWI_mean",
            error_y="NDWI_std",
            markers=True,
            color_discrete_sequence=["#1E88E5"],
        )
    else:
        fig = px.line(
            df,
            x="date",
            y="NDWI_mean",
            markers=True,
            color_discrete_sequence=["#1E88E5"],
        )

    fig.update_traces(
        line=dict(width=3),
        hovertemplate="Date: %{x}<br>NDWI: %{y:.3f}<extra></extra>",
    )

    mean_value = df["NDWI_mean"].mean()
    fig.add_hline(
        y=mean_value,
        line_dash="dash",
        line_color="grey",
        annotation_text=f"Mean NDWI = {mean_value:.3f}",
        annotation_position="bottom right",
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="NDWI",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(showline=True, linewidth=1, linecolor="black"),
        yaxis=dict(showline=True, linewidth=1, linecolor="black"),
    )
    st.write(":blue[NDWI Mean Over Time]")
    st.plotly_chart(fig, use_container_width=True)


# --------------------------
# Assemble NDWI Dashboard
# --------------------------
def ndwi(data, selected_years, show_var, map_view):
    df = data
    if not selected_years or set(selected_years) == {2022, 2023, 2024}:
        years_text = "2022 - 2023"
    else:
        years_text = " - ".join(str(y) for y in selected_years)

    st.markdown(
        f"<h1 style='text-align: center; margin-top: -40px;'>💧 Normalized Difference Water Index ({years_text})</h1>",
        unsafe_allow_html=True,
    )
    st.write("---")

    aoi_json = json.loads(load_aoi_data())

    left, mid, right = st.columns([30, 45, 25], gap="small")

    # ---------------- Left Column ----------------
    with left:
        with st.container(border=True):
            render_aoi_map(aoi_json, map_type=map_view)

        metric_left, metric_right = st.columns([5, 5], gap="small")

        with metric_left:
            with st.container(border=True):
                mean_val = f"{df['NDWI_mean'].mean():.3f}"
                st.markdown(
                    f"<div style='text-align:center;'><h3>Mean NDWI</h3><p style='font-size:26px'>{mean_val}</p></div>",
                    unsafe_allow_html=True,
                )

            with st.container(border=True):
                max_val = f"{df['NDWI_mean'].max():.3f}"
                st.markdown(
                    f"<div style='text-align:center;'><h3>Max NDWI</h3><p style='font-size:26px'>{max_val}</p></div>",
                    unsafe_allow_html=True,
                )

            with st.container(border=True):
                count_val = f"{df['count'].iloc[-1]:,}"
                st.markdown(
                    f"<div style='text-align:center;'><h3>Pixel Count</h3><p style='font-size:26px'>{count_val}</p></div>",
                    unsafe_allow_html=True,
                )

        with metric_right:
            with st.container(border=True):
                min_val = f"{df['NDWI_mean'].min():.3f}"
                st.markdown(
                    f"<div style='text-align:center;'><h3>Min NDWI</h3><p style='font-size:26px'>{min_val}</p></div>",
                    unsafe_allow_html=True,
                )

            with st.container(border=True):
                std_val = f"{df['NDWI_mean'].std():.3f}"
                st.markdown(
                    f"<div style='text-align:center;'><h3>NDWI Std Dev</h3><p style='font-size:26px'>{std_val}</p></div>",
                    unsafe_allow_html=True,
                )

            with st.container(border=True):
                timeline_val = f"{df['date'].min().year} → {df['date'].max().year}"
                st.markdown(
                    f"<div style='text-align:center;'><h3>Timeline</h3><p style='font-size:26px'>{timeline_val}</p></div>",
                    unsafe_allow_html=True,
                )

    # ---------------- Middle Column ----------------
    with mid:
        with st.container(border=True):
            plot_ndwi(df, show_var)
        with st.container(border=True):
            plot_ndwi_heatmap_plotly(df)

    # ---------------- Right Column ----------------
    with right:
        with st.container(border=True):
            show_data(df)
        show_ndwi_trend(df)
