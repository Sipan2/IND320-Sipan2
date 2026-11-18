import streamlit as st

st.set_page_config(page_title="IND320 | Reservoirs", layout="wide")
# Keep every page, including the home page, in the same folder.
page = st.navigation({
    "Overview": [st.Page("pages/0_Home.py", title="Reservoir map", default=True),
                 st.Page("pages/1_Data_table.py", title="Data table"),
                 st.Page("pages/2_Plots.py", title="Reservoir measurements"),
                 st.Page("pages/3_Electricity_transfers.py", title="Electricity transfers")],
    "Patterns and data quality": [st.Page("pages/5_Reservoir_patterns.py", title="Reservoir patterns"),
                                  st.Page("pages/6_Weather_quality.py", title="Weather data quality"),
                                  st.Page("pages/8_Weather_links.py", title="Weather and filling")],
    "Prediction": [st.Page("pages/7_Forecast.py", title="Reservoir forecast")],
})
page.run()
