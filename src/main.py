import streamlit as st
from streamlit_option_menu import option_menu
from Dashboards.lst_dashboard import lst
from Dashboards.ndvi_dashboard import ndvi
from Dashboards.ndwi_dashboard import ndwi
from Dashboards.ndbi_dashboard import ndbi
from data_loader import load_data

df = load_data()


def main():
    st.set_page_config(page_title="Mach24 Orbitals", page_icon="🛰️", layout="wide")

    # Sidebar navigation
    with st.sidebar:
        selected = option_menu(
            menu_title="Dashboards",
            options=["NDVI", "NDWI", "NDBI", "LST"],
            icons=["tree", "droplet", "building", "sun"],
            menu_icon="list",
            default_index=0,
        )

        map_view = st.radio("Map View", ["Standard", "Satellite"])
        # ---------------- Multi-Select Year Selector ----------------
        years = [2022, 2023, 2024]
        selected_years = st.multiselect(
            "Select Year(s)",
            options=years,
            default=years,  # default to all selected
        )

        # If nothing selected, fallback to all years
        if not selected_years:
            df_filtered = df.copy()
        else:
            df_filtered = df[df["year"].isin(selected_years)]

        # Sidebar radio to toggle variability
        show_var = st.radio("Show Variability?", ["Yes", "No"]) == "Yes"

    # Routing
    if selected == "NDVI":
        ndvi(
            data=df_filtered,
            selected_years=selected_years,
            show_var=show_var,
            map_view=map_view,
        )
    elif selected == "NDWI":
        ndwi(
            data=df_filtered,
            selected_years=selected_years,
            show_var=show_var,
            map_view=map_view,
        )
    elif selected == "NDBI":
        ndbi(
            data=df_filtered,
            selected_years=selected_years,
            show_var=show_var,
            map_view=map_view,
        )
    elif selected == "LST":
        lst(
            data=df_filtered,
            selected_years=selected_years,
            show_var=show_var,
            map_view=map_view,
        )
    else:
        st.warning("Select a valid dashboard from the sidebar.")


if __name__ == "__main__":
    main()
