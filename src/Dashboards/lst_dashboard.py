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
# LST Rate Change
# --------------------------
def show_lst_trend(df):
    """
    Displays the LST trend as an area chart in a Streamlit metric.
    The delta shows the change between the last two measurements.

    Parameters:
    - df: DataFrame with columns 'date' and 'LST_mean_C'
    """
    df = df.sort_values("date")
    lst_mean = df["LST_mean_C"].values

    if len(lst_mean) < 2:
        st.metric(
            "LST Trend",
            round(lst_mean[-1], 2) if len(lst_mean) > 0 else "N/A",
            "N/A",
            chart_data=lst_mean,
            chart_type="line",
            border=True,
        )
        return

    recent_delta = round(lst_mean[-1] - lst_mean[-2], 2)
    chart_data = lst_mean

    st.metric(
        "LST Trend",
        round(lst_mean[-1], 2),
        recent_delta,
        chart_data=chart_data,
        chart_type="line",
        border=True,
    )

    st.metric(
        "LST Trend",
        round(lst_mean[-1], 2),
        recent_delta,
        chart_data=chart_data,
        chart_type="area",
        border=True,
    )


# --------------------------
# LST Seasonal Heatmap
# --------------------------
def plot_lst_heatmap_plotly(df: pd.DataFrame, width: int = 700, height: int = 370):
    """Plot interactive LST seasonal heatmap for years using Plotly."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])

    if "month_num" not in df.columns:
        df["month_num"] = df["date"].dt.month

    heatmap_df = df.pivot_table(index="year", columns="month_num", values="LST_mean_C")
    heatmap_df = heatmap_df.reindex(columns=range(1, 13))

    month_labels = [calendar.month_abbr[i] for i in range(1, 13)]

    fig = px.imshow(
        heatmap_df,
        labels=dict(x="Month", y="Year", color="LST (°C)"),
        x=month_labels,
        color_continuous_scale="RdYlBu_r",
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
    st.write(":red[LST Seasonal Heatmap]")
    st.plotly_chart(fig, use_container_width=True)


# --------------------------
# Show Data Table
# --------------------------
def show_data(df: pd.DataFrame, width: int = 700, height: int = 450):
    show_cols = ["date", "LST_mean_C", "LST_std_C"]
    st.write(":red[LST Data]")
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
# LST Line Chart
# --------------------------
def plot_lst(df: pd.DataFrame, show_var: bool):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    if show_var:
        fig = px.line(
            df,
            x="date",
            y="LST_mean_C",
            error_y="LST_std_C",
            markers=True,
            color_discrete_sequence=["#D32F2F"],
        )
    else:
        fig = px.line(
            df,
            x="date",
            y="LST_mean_C",
            markers=True,
            color_discrete_sequence=["#D32F2F"],
        )

    fig.update_traces(
        line=dict(width=3),
        hovertemplate="Date: %{x}<br>LST: %{y:.2f}°C<extra></extra>",
    )

    mean_value = df["LST_mean_C"].mean()
    fig.add_hline(
        y=mean_value,
        line_dash="dash",
        line_color="grey",
        annotation_text=f"Mean LST = {mean_value:.2f}°C",
        annotation_position="bottom right",
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="LST (°C)",
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis=dict(showline=True, linewidth=1, linecolor="black"),
        yaxis=dict(showline=True, linewidth=1, linecolor="black"),
    )
    st.write(":red[LST Over Time]")
    st.plotly_chart(fig, use_container_width=True)


# --------------------------
# Assemble LST Dashboard
# --------------------------
def lst(data, selected_years, show_var, map_view):
    df = data
    if not selected_years or set(selected_years) == {2022, 2023, 2024}:
        years_text = "2022 - 2023"
    else:
        years_text = " - ".join(str(y) for y in selected_years)

    st.markdown(
        f"<h1 style='text-align: center; margin-top: -40px;'>🌡️ Land Surface Temperature ({years_text})</h1>",
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
                mean_val = f"{df['LST_mean_C'].mean():.2f} °C"
                st.markdown(
                    f"<div style='text-align:center;'><h3>Mean LST</h3><p style='font-size:26px'>{mean_val}</p></div>",
                    unsafe_allow_html=True,
                )

            with st.container(border=True):
                max_val = f"{df['LST_mean_C'].max():.2f} °C"
                st.markdown(
                    f"<div style='text-align:center;'><h3>Max LST</h3><p style='font-size:26px'>{max_val}</p></div>",
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
                min_val = f"{df['LST_mean_C'].min():.2f} °C"
                st.markdown(
                    f"<div style='text-align:center;'><h3>Min LST</h3><p style='font-size:26px'>{min_val}</p></div>",
                    unsafe_allow_html=True,
                )

            with st.container(border=True):
                std_val = f"{df['LST_mean_C'].std():.2f} °C"
                st.markdown(
                    f"<div style='text-align:center;'><h3>LST Std Dev</h3><p style='font-size:26px'>{std_val}</p></div>",
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
            plot_lst(df, show_var)
        with st.container(border=True):
            plot_lst_heatmap_plotly(df)

    # ---------------- Right Column ----------------
    with right:
        with st.container(border=True):
            show_data(df)
        show_lst_trend(df)
