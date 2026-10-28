import streamlit as st
from ind320.data_utils import load_data

st.title("Reservoirs over time")
st.write("IND320 - Part 3: Data quality")
st.write("Explore reservoir filling levels and stored energy in Norway. "
         "The data comes directly from NVE and is updated weekly.")
data = load_data()
st.write(f"The dataset contains {len(data):,} observations, from "
         f"{data.date.min():%d %B %Y} to {data.date.max():%d %B %Y}.")
st.write("Open Plots to compare regions and measurements, or Data table "
         "to inspect the weekly observations and area sparklines.")
st.write("Open Electricity transfers to compare imports and exports on nine international connections. "
         "The ENTSO-E data covers October 2024 to September 2026 and is read from MongoDB.")
st.markdown("[NVE reservoir statistics](https://www.nve.no/energi/analyser-og-statistikk/magasinstatistikk/)")
st.write("Reservoir patterns adds STL decomposition and a spectrogram. Weather data quality explores "
         "ERA5 precipitation and temperature with SPC and Local Outlier Factor. "
         "The complete NO3 dataset for 2024 is available; VASS selections use the assignment’s east, west and north weather regions.")
