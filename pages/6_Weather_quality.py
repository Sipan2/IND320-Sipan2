import matplotlib.pyplot as plt
import streamlit as st

from ind320.quality_analysis import precipitation_spc, temperature_lof
from ind320.quality_ui import weather_control

st.title('Weather data quality')
weather = weather_control()
spc_tab, lof_tab = st.tabs(['Statistical process control', 'Local Outlier Factor'])

with spc_tab:
    st.write('DCT filtering separates slower variation from short-term residuals. Robust limits use '
             'the median and median absolute deviation of the whole selected year. Flagged values '
             'are unusual under this rule; they are not automatically measurement errors.')
    cutoff_period = st.slider('Cut-off period (days)', 2, 120, 30)
    deviations = st.slider('Robust standard deviations', 1.0, 8.0, 3.0, step=0.25)
    if weather is not None:
        result = precipitation_spc(weather.precipitation, cutoff_cycles_per_day=1 / cutoff_period, deviations=deviations)
        chart = result.data[["precipitation_mm", "lower_mm", "upper_mm"]].copy()
        chart["Flagged"] = chart.precipitation_mm.where(result.data.outlier)
        st.line_chart(chart.drop(columns="Flagged"))
        st.scatter_chart(chart[["Flagged"]].dropna())
        plt.close(result.figure)
        st.metric('Flagged hours', result.summary['outliers'])
        st.caption(f'{result.summary["outlier_fraction"]:.1%} of hours; robust residual scale '
                   f'{result.summary["robust_sigma_mm"]:.3f} mm. No values are removed.')
        with st.expander('Flagged observations'):
            st.dataframe(result.data.loc[result.data.outlier], width='stretch')

with lof_tab:
    st.write('Local Outlier Factor compares values and hourly changes with neighbours in '
             'standardised feature space. Neighbours are similar feature pairs, not a moving time window. '
             'The initial hour cannot be evaluated because its preceding change is unavailable.')
    contamination = st.slider('Target anomaly proportion (%)', 0.1, 10.0, 1.0, step=0.1) / 100
    neighbours = st.slider('LOF neighbours', 5, 100, 20)
    if weather is not None:
        property_name = st.selectbox("Weather property", ["temperature_2m", "precipitation"])
        result = temperature_lof(weather[property_name], contamination=contamination, neighbours=neighbours)
        chart = weather[[property_name]].copy()
        st.line_chart(chart)
        st.scatter_chart(chart.loc[result.data.anomaly])
        plt.close(result.figure)
        st.metric('Anomalous hours', result.summary['anomalies'])
        st.caption(f'{result.summary["actual_fraction"]:.1%} of {result.summary["evaluated"]:,} evaluated hours. '
                   'The requested proportion sets a threshold rather than establishing an error rate.')
        with st.expander('Anomalous observations'):
            st.dataframe(result.data.loc[result.data.anomaly].rename(columns={"temperature_c": property_name, "change_c": "Hourly change"}), width='stretch')
