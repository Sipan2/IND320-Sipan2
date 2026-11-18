import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ind320.currency_data import download_exchange_rates
from ind320.data_utils import load_data, reservoir_controls, select_area
from ind320.forecast import forecast_filling

st.title("Reservoir forecast")
data = load_data()
interval, family = reservoir_controls(data)
selected, area = select_area(interval)
series = selected.sort_values("date").set_index("date").filling_ratio
weeks = st.slider("Forecast horizon (weeks)", 1, 26, 12)
lags = st.slider("Previous weeks used by the model", 1, 12, 8)
rate = st.select_slider("Learning rate", options=[0.001, 0.005, 0.01, 0.02], value=0.01)
currencies = st.multiselect("Exchange rates to include", ["EUR", "USD"])
rates = st.cache_data(ttl=86400)(download_exchange_rates)
try:
    inputs = None
    if currencies:
        daily = rates(series.index.min(), series.index.max())
        inputs = daily[currencies].resample("W-SUN").last()
    forecast = forecast_filling(series, len(series), weeks, lags, rate, inputs)
except (OSError, ValueError) as error:
    st.warning(str(error))
    st.stop()

# Reveal one forecast week per frame while keeping the historical line in view.
fig = go.Figure()
fig.add_scatter(x=series.index, y=100 * series, name="Observed")
fig.add_scatter(x=forecast.index, y=100 * forecast, name="Forecast")
fig.frames = [go.Frame(data=[go.Scatter(x=forecast.index[:i], y=100 * forecast.iloc[:i])],
                       traces=[1]) for i in range(1, weeks + 1)]
fig.update_layout(yaxis_title="Reservoir filling (%)", title=area,
                  updatemenus=[dict(type="buttons", buttons=[dict(label="Play forecast",
                  method="animate", args=[None, {"fromcurrent": False}])])])
st.plotly_chart(fig)
st.caption("Each forecast week uses the preceding predictions. Selected exchange rates stay at their last observed values.")
