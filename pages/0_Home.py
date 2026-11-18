"""Choose the region and time interval shared by the reservoir pages."""
import json
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from ind320.data_utils import load_data
from ind320.area_mapping import VASS_WEATHER_REGIONS

ROOT = Path(__file__).resolve().parents[1]
st.title("Norwegian reservoirs")
data = load_data()
mode = st.radio("Colour by", ["Price area", "Water area", "Weather property"], horizontal=True)
family = "VASS" if mode == "Water area" else "EL"
file, field = ("assignment_precipitation", "region") if family == "VASS" else ("electricity", "ElSpotOmr")
months = sorted(data.date.dt.strftime("%Y-%m").unique())
default = st.session_state.get("nve_interval", ("2024-01", "2024-12"))
default = tuple(default)
start, end = st.select_slider("Observation period", months, value=default)
st.session_state["nve_interval"] = start, end
st.session_state["forecast_weeks"] = st.slider("Forecast horizon (weeks)", 1, 26, st.session_state.get("forecast_weeks", 12))
subset = data.loc[data.area_type.eq(family) & data.date.dt.strftime("%Y-%m").between(start, end)]
geo = json.loads((ROOT / f"data/regions/{file}.geojson").read_text())
ids = [item["properties"][field] for item in geo["features"]]
numbers = {label: number for number, label in VASS_WEATHER_REGIONS.items()} if family == "VASS" else {label: int(label[2:]) for label in ids}
values = subset.groupby("area_number").filling_ratio.mean().mul(100)
unit = "Mean filling (%)"
if mode == "Weather property":
    var = st.selectbox("Weather property", ["temperature_2m", "precipitation"])
    unit = "Mean temperature (°C)" if var == "temperature_2m" else "Mean hourly precipitation (mm)"
    values = {}
    for label, number in numbers.items():
        paths = sorted((ROOT / "data/weather").glob(f"electricity_{label}_*.parquet"))
        if paths:
            frame = pd.concat([pd.read_parquet(p) for p in paths]).drop_duplicates("time_utc")
            month = pd.to_datetime(frame.time_utc, utc=True).dt.tz_convert("Europe/Oslo").dt.strftime("%Y-%m")
            values[number] = frame.loc[month.between(start, end), var].mean()
    st.caption("Only areas with saved weather observations are coloured.")
chosen = st.session_state.get("map_area", ("EL", 3))
fig = go.Figure(go.Choropleth(geojson=geo, featureidkey="properties."+field, locations=ids,
    z=[values.get(numbers[label], float("nan")) for label in ids], colorscale="Blues",
    colorbar_title=unit, marker_opacity=0.7,
    marker_line_width=[3 if chosen == (family, numbers[label]) else 1 for label in ids]))
fig.update_geos(fitbounds="locations", visible=False)
fig.update_layout(clickmode="event+select", margin=dict(l=0,r=0,t=0,b=0))
event = st.plotly_chart(fig, key="reservoir_map_"+family, on_select="rerun")
points = event.selection.points
if points:
    point = points[-1]
    label = point.get("location") or ids[point["point_index"]]
    selection = family, numbers[label]
    if chosen != selection:
        st.session_state.update(map_area=selection, nve_type=family)
        st.rerun()
st.caption(f"Selected reservoir area: {chosen[0]} {chosen[1]}.")
