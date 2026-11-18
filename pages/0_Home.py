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
map_panel, controls = st.columns([2, 1], gap="large")
controls.subheader("Map settings")
mode = controls.radio("Colour by", ["Price area", "Water area", "Weather property"])
family = "VASS" if mode == "Water area" else "EL"
file, field = ("assignment_precipitation", "region") if family == "VASS" else ("electricity", "ElSpotOmr")
months = sorted(data.date.dt.strftime("%Y-%m").unique())
default = st.session_state.get("nve_interval", ("2024-01", "2024-12"))
left, right = controls.columns(2)
start = left.selectbox("From month", months, index=months.index(default[0]))
end_months = [month for month in months if month >= start]
end = right.selectbox("Through month", end_months, index=end_months.index(max(start, default[1])))
st.session_state["nve_interval"] = start, end
with controls.expander("Forecast settings"):
    st.session_state["forecast_weeks"] = st.slider("Forecast horizon (weeks)", 1, 26, st.session_state.get("forecast_weeks", 12))
subset = data.loc[data.area_type.eq(family) & data.date.dt.strftime("%Y-%m").between(start, end)]
geo = json.loads((ROOT / f"data/regions/{file}.geojson").read_text())
ids = [item["properties"][field] for item in geo["features"]]
numbers = {label: number for number, label in VASS_WEATHER_REGIONS.items()} if family == "VASS" else {label: int(label[2:]) for label in ids}
values = subset.groupby("area_number").filling_ratio.mean().mul(100)
unit = "Mean filling (%)"
if mode == "Weather property":
    var = controls.selectbox("Weather property", ["temperature_2m", "precipitation"])
    unit = "Mean temperature (°C)" if var == "temperature_2m" else "Mean hourly precipitation (mm)"
    values = {}
    for label, number in numbers.items():
        paths = sorted((ROOT / "data/weather").glob(f"electricity_{label}_*.parquet"))
        if paths:
            frame = pd.concat([pd.read_parquet(p) for p in paths]).drop_duplicates("time_utc")
            month = pd.to_datetime(frame.time_utc, utc=True).dt.tz_convert("Europe/Oslo").dt.strftime("%Y-%m")
            values[number] = frame.loc[month.between(start, end), var].mean()
    controls.caption("Only areas with saved weather observations are coloured.")
chosen = st.session_state.get("map_area", ("EL", 3))
if chosen[0] != family:
    chosen = (family, 3 if family == "EL" else 1)
    st.session_state.update(map_area=chosen, nve_type=family)

fig = go.Figure(go.Choroplethmap(geojson=geo, featureidkey="properties."+field, locations=ids,
    z=[values.get(numbers[label], float("nan")) for label in ids], colorscale="Blues",
    colorbar=dict(title=unit, orientation="h", len=0.50, thickness=10, y=-0.09, yanchor="top"),
    hovertemplate="%{location}<br>" + unit + ": %{z:.2f}<extra></extra>",
    marker_opacity=0.82,
    marker_line_color=["#FFAD75" if chosen == (family, numbers[label]) else "#92A9BC" for label in ids],
    marker_line_width=[3 if chosen == (family, numbers[label]) else 1 for label in ids]))
# Fit mainland Norway, including Finnmark, in the initial viewport.
fig.update_layout(map=dict(style="carto-darkmatter", center=dict(lat=65.2, lon=18), zoom=3.25,
                           bearing=0))
fig.update_layout(clickmode="event+select", height=655, margin=dict(l=4,r=4,t=8,b=130))
map_panel.caption("Select an area on the map to use it on the analysis pages.")
event = map_panel.plotly_chart(fig, key="reservoir_map_"+family, on_select="rerun")
points = event.selection.points
if points:
    point = points[-1]
    label = point.get("location") or ids[point["point_index"]]
    selection = family, numbers[label]
    if chosen != selection:
        st.session_state.update(map_area=selection, nve_type=family)
        st.rerun()
region_name = next(label for label, number in numbers.items() if number == chosen[1])
value = values.get(chosen[1], float("nan"))
controls.subheader(region_name if family == "EL" else region_name.title())
controls.metric(unit, f"{value:.1f}" if pd.notna(value) else "No observations")
controls.page_link("pages/7_Forecast.py", label="Open reservoir forecast")
