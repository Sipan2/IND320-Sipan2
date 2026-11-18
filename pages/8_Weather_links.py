"""Compare local calendar weeks across the two data sources."""
import streamlit as st
from ind320.data_utils import load_data
from ind320.quality_ui import weather_control
from ind320.weekly_weather import weekly_weather, sliding_correlation

st.title("Weather and reservoir filling")
weather = weather_control()
if weather is None:
    st.stop()
family = st.session_state["nve_type"]
number = st.session_state["quality_weather_area"]
data = load_data()
filling = data.loc[data.area_type.eq(family) & data.area_number.eq(number)].set_index("date").filling_ratio
variable = st.selectbox("Weather property", ["temperature_2m", "precipitation"])
lag = st.slider("Weather leads filling by (weeks)", 0, 12, 1)
window = st.slider("Correlation window (weeks)", 4, 26, 12)
weekly = st.cache_data(show_spinner=False)(weekly_weather)(weather)
result = sliding_correlation(filling, weekly[variable], lag, window)
if result.empty:
    st.info("There are too few complete overlapping weeks for this window.")
else:
    st.line_chart(result.rename("Correlation"), y_label="Pearson correlation")
