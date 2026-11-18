"""Fit the model to the selected area and animate its weekly forecasts."""
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ind320.currency_data import download_exchange_rates
from ind320.data_utils import load_data, reservoir_controls, select_area
from ind320.forecast import forecast_filling
from ind320.area_mapping import weather_region
from ind320.weekly_weather import weekly_weather

st.title("Reservoir forecast")
data = load_data()
interval, family = reservoir_controls(data)
selected, area = select_area(interval)
series = selected.sort_values("date").set_index("date").filling_ratio
weeks = st.slider("Forecast horizon (weeks)", 1, 26, st.session_state.get("forecast_weeks", 12))
st.session_state["forecast_weeks"] = weeks
lags = st.slider("Previous weeks used by the model", 1, 12, 8)
rate = st.select_slider("Learning rate", options=[0.001, 0.005, 0.01, 0.02], value=0.01)
currencies = st.multiselect("Exchange rates to include", ["EUR", "USD"])
weather_vars = st.multiselect("Weather inputs", ["temperature_2m", "precipitation"])
rates = st.cache_data(ttl=86400)(download_exchange_rates)
try:
    inputs = None
    if currencies:
        daily = rates(series.index.min(), series.index.max())
        inputs = daily[currencies].resample("W-SUN").last()
    if weather_vars:
        kind, region = weather_region(family, int(selected.area_number.iloc[0]))
        folder = Path(__file__).resolve().parents[1] / "data/weather"
        paths = sorted(folder.glob(f"{kind}_{region}_*.parquet"))
        if not paths:
            raise ValueError("Fetch regional observations on the weather page first.")
        hourly = pd.concat([pd.read_parquet(path) for path in paths]).drop_duplicates("time_utc")
        weather = weekly_weather(hourly.set_index("time_utc"))[weather_vars]
        if series.index[-1] - weather.dropna().index.max() > pd.Timedelta(days=7):
            raise ValueError("Choose a training period that ends within the saved weather record.")
        inputs = weather if inputs is None else inputs.join(weather, how="outer")
    forecast = forecast_filling(series, len(series), weeks, lags, rate, inputs)
except (OSError, ValueError) as error:
    st.warning(str(error))
    st.stop()

# Reveal one forecast week per frame while keeping the historical line in view.
fig = go.Figure()
fig.add_scatter(x=series.index, y=100 * series, name="Observed", line=dict(color="#77C8FF"))
fig.add_scatter(x=forecast.index, y=100 * forecast, name="Forecast", line=dict(color="#FFAD75", dash="dash"), mode="lines+markers")
fig.frames = [go.Frame(data=[go.Scatter(x=forecast.index[:i], y=100 * forecast.iloc[:i])],
                       traces=[1]) for i in range(1, weeks + 1)]
fig.update_layout(yaxis_title="Reservoir filling (%)", title=f"Reservoir filling · {area}", hovermode="x unified",
                  updatemenus=[dict(type="buttons", buttons=[dict(label="Play forecast",
                  method="animate", args=[None, {"fromcurrent": False}])])])
st.plotly_chart(fig)
st.caption("Each forecast week uses the preceding predictions. Selected external inputs stay at their last observed values.")
