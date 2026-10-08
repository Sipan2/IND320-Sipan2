import streamlit as st
from data_utils import load_data

st.title("Reservoirs over time")
st.write("IND320 - Part 2")
st.write("Explore reservoir filling levels and stored energy in Norway. "
         "The data comes directly from NVE and is updated weekly.")
data = load_data()
st.write(f"The dataset contains {len(data):,} observations, from "
         f"{data.date.min():%d %B %Y} to {data.date.max():%d %B %Y}.")
st.write("Use NVE areas to compare regions, or open Data table and Plots "
         "to look more closely at one area.")
st.write("Open Electricity transfers to compare imports and exports on nine international connections. "
         "The ENTSO-E data covers October 2024 to September 2026 and is read from MongoDB.")
st.markdown("[NVE reservoir statistics](https://www.nve.no/energi/analyser-og-statistikk/magasinstatistikk/)")
