from pathlib import Path
import streamlit as st
from data_utils import load_data

# Files in the pages folder automatically appear in the sidebar.
st.set_page_config(page_title="IND320 | Reservoirs", layout="wide")
st.title("Reservoirs over time")
st.write("IND320 - Part 1")
st.write("Here I explore filling level and stored energy in reservoirs. "
         "Choose Data table or Plots from the menu on the left.")
data = load_data()
st.write(f"The dataset has {len(data):,} rows, from {data.date.min():%d.%m.%Y} "
         f"to {data.date.max():%d.%m.%Y}.")
st.info("The file contains several area types. Select one area at a time on the analysis pages.")
st.markdown("[Data source: IND320 / D2Dbook](https://github.com/khliland/IND320/blob/main/D2Dbook/data/reservoirs.csv)")
st.caption("This app is part of the IND320 course project.")

# Play the screencast stored with the project, without a separate download.
st.header("Screencast", anchor="screencast")
st.write("A short walkthrough of the app and code. Press play to watch.")
st.video(str(Path(__file__).parent / "IND320-Part-1-screencast.mp4"))
st.markdown("[Download the video from GitHub](https://github.com/Sipan2/IND320-Sipan2/raw/refs/heads/main/IND320-Part-1-screencast.mp4)")
