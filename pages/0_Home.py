"""Choose the region and time interval shared by the reservoir pages."""
import json
from pathlib import Path
import pandas as pd
from branca.colormap import LinearColormap
from ind320.map_component import boundary_payload, reservoir_map
import streamlit as st
from ind320.data_utils import load_data
from ind320.area_mapping import VASS_WEATHER_REGIONS

ROOT = Path(__file__).resolve().parents[1]
@st.cache_data(show_spinner=False)
def map_months(dates):
    return dates.dt.strftime("%Y-%m")


@st.cache_data(show_spinner=False)
def read_boundaries(path, modified_ns):
    # The file timestamp invalidates the cache when boundaries are replaced.
    return json.loads(Path(path).read_text())


@st.cache_data(show_spinner=False)
def read_weather(files):
    frame = pd.concat([pd.read_parquet(path) for path, modified_ns in files]).drop_duplicates("time_utc")
    frame["map_month"] = pd.to_datetime(frame.time_utc, utc=True).dt.tz_convert("Europe/Oslo").dt.strftime("%Y-%m")
    return frame


st.title("Norwegian reservoirs")
data = load_data()
map_panel, controls = st.columns([2, 1], gap="large")
controls.subheader("Map settings")
mode = controls.radio("Colour by", ["Price area", "Water area", "Weather property"])
family = "VASS" if mode == "Water area" else "EL"
file, field = ("assignment_precipitation", "region") if family == "VASS" else ("electricity", "ElSpotOmr")
month_labels = map_months(data.date)
months = sorted(month_labels.unique())
default = st.session_state.get("nve_interval", ("2023-01", "2024-12"))
left, right = controls.columns(2)
start = left.selectbox("From month", months, index=months.index(default[0]))
end_months = [month for month in months if month >= start]
end = right.selectbox("Through month", end_months, index=end_months.index(max(start, default[1])))
st.session_state["nve_interval"] = start, end
with controls.expander("Forecast settings"):
    st.session_state["forecast_weeks"] = st.slider("Forecast horizon (weeks)", 1, 26, st.session_state.get("forecast_weeks", 12))
subset = data.loc[data.area_type.eq(family) & month_labels.between(start, end)]
boundary_path = ROOT / f"data/regions/{file}.geojson"
geo = read_boundaries(str(boundary_path), boundary_path.stat().st_mtime_ns)
ids = [item["properties"][field] for item in geo["features"]]
numbers = {label: number for number, label in VASS_WEATHER_REGIONS.items()} if family == "VASS" else {label: int(label[2:]) for label in ids}
values = subset.groupby("area_number").filling_ratio.mean().mul(100)
unit = "Mean filling (%)"
if mode == "Weather property":
    var = controls.selectbox("Weather property", ["temperature_2m", "precipitation"],
                             format_func=lambda name: "Temperature" if name == "temperature_2m" else "Precipitation")
    unit = "Mean temperature (°C)" if var == "temperature_2m" else "Mean hourly precipitation (mm)"
    values = {}
    for label, number in numbers.items():
        paths = sorted((ROOT / "data/weather").glob(f"electricity_{label}_*.parquet"))
        if paths:
            frame = read_weather(tuple((str(p), p.stat().st_mtime_ns) for p in paths))
            month = frame["map_month"]
            values[number] = frame.loc[month.between(start, end), var].mean()
    controls.caption("Only areas with saved weather observations are coloured.")
chosen = st.session_state.get("map_area", ("EL", 3))
if chosen[0] != family or chosen[1] not in numbers.values():
    chosen = (family, 3 if family == "EL" else 1)
    st.session_state.update(map_area=chosen, nve_type=family)

# Leaflet reports polygon clicks directly, including areas without weather values.
finite = [float(values.get(number)) for number in numbers.values()
          if pd.notna(values.get(number))]
low, high = (min(finite), max(finite)) if finite else (0.0, 1.0)
if low == high:
    low, high = low - 0.5, high + 0.5
colours = LinearColormap(["#BFDDF3", "#529BC8", "#14517D"], vmin=low, vmax=high)
areas = {}
for label, number in numbers.items():
    value = values.get(number, float("nan"))
    areas[label] = {
        "unit": unit,
        "value": f"{value:.2f}" if pd.notna(value) else "No observations",
        "style": {"fillColor": colours(value) if pd.notna(value) else "#465361",
                  "fillOpacity": 0.65 if pd.notna(value) else 0.20},
    }
view = st.session_state.get("reservoir_map_view", {})

def update_map_selection():
    # Component callbacks run before the page, so one render updates the outline.
    event = st.session_state.get("reservoir_map") or {}
    if event.get("center") and event.get("zoom"):
        st.session_state["reservoir_map_view"] = {
            "center": [event["center"]["lat"], event["center"]["lng"]], "zoom": event["zoom"]}
    label = event.get("label") if event.get("field") == field else None
    if label in numbers and chosen != (family, numbers[label]):
        st.session_state.update(map_area=(family, numbers[label]), nve_type=family)

with map_panel:
    st.caption("Click anywhere inside an area to use it on the analysis pages.")
    reservoir_map(
        boundary=boundary_payload(str(boundary_path), boundary_path.stat().st_mtime_ns),
        field=field, areas=areas,
        selected=next(label for label, number in numbers.items() if number == chosen[1]),
        view=view, on_change=update_map_selection,
    )
    # Keep the legend below the map, clear of the geographic outlines.
    st.markdown(f"<div style='max-width:440px;margin:12px auto 0'>"
                f"<div style='height:10px;background:linear-gradient(to right,#BFDDF3,#529BC8,#14517D);border-radius:3px'></div>"
                f"<div style='display:flex;justify-content:space-between;font-size:0.85rem'><span>{low:.1f}</span><span>{unit}</span><span>{high:.1f}</span></div></div>",
                unsafe_allow_html=True)
region_name = next(label for label, number in numbers.items() if number == chosen[1])
value = values.get(chosen[1], float("nan"))
controls.subheader(region_name if family == "EL" else region_name.title())
controls.metric(unit, f"{value:.1f}" if pd.notna(value) else "No observations")
controls.page_link("pages/7_Forecast.py", label="Open reservoir forecast")
