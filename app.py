import streamlit as st

st.set_page_config(page_title="IND320 | Reservoirs", layout="wide")
# Keep every page, including the home page, in the same folder.
page = st.navigation([
    st.Page("pages/0_Home.py", title="Home", default=True),
    st.Page("pages/1_Data_table.py", title="Data table"),
    st.Page("pages/2_Plots.py", title="Plots"),
    st.Page("pages/3_Electricity_transfers.py", title="Electricity transfers"),
    st.Page("pages/5_Reservoir_patterns.py", title="Reservoir patterns"),
    st.Page("pages/6_Weather_quality.py", title="Weather data quality"),
])
page.run()
