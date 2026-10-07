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
st.info("The electricity transfer analysis is still in progress while ENTSO-E API access is pending.")
st.markdown("[NVE reservoir statistics](https://www.nve.no/energi/analyser-og-statistikk/magasinstatistikk/)")
