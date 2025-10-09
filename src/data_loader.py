import os
import geopandas as gpd
import pandas as pd
import streamlit as st


BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # /app/src
AOI_PATH = os.path.join(BASE_DIR, "..", "data", "aoi.geojson")
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "all-landsat-data.csv")


def load_aoi_data():
    gdf = gpd.read_file(AOI_PATH)
    # Ensure CRS is WGS84
    if gdf.crs is None:
        gdf.set_crs(epsg=4326, inplace=True)
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)
    return gdf.to_json()


@st.cache_data
def load_data():
    data = pd.read_csv(DATA_PATH)
    data["date"] = pd.to_datetime(data["date"])
    return data
