import matplotlib.pyplot as plt
import streamlit as st

from ind320.quality_analysis import filling_stl, filling_spectrogram
from ind320.quality_ui import filling_control

st.title('Reservoir patterns')
series = filling_control()
stl_tab, spectrum_tab = st.tabs(['STL decomposition', 'Spectrogram'])

with stl_tab:
    st.write('Separate filling levels into trend, seasonal variation and a residual. '
             'A 52-week seasonal period approximates a calendar year.')
    seasonal = st.slider('Seasonal smoother', 7, 51, 13, step=2)
    trend = st.slider('Trend smoother (weeks)', 53, 157, 81, step=2)
    robust = st.checkbox('Use robust fitting', value=True)
    try:
        result = filling_stl(series, seasonal=seasonal, trend=trend, robust=robust)
        st.pyplot(result.figure)
        plt.close(result.figure)
        st.caption(f'{result.summary["observations"]:,} weekly observations. Components use filling fractions, '
                   'so 0.1 corresponds to ten percentage points.')
    except ValueError as error:
        st.warning(str(error))

with spectrum_tab:
    st.write('Inspect how the strength of recurring variation changes over time. '
             'Longer windows improve frequency resolution but blur changes in time.')
    window = st.slider('Window length (weeks)', 52, 208, 104, step=13)
    overlap = st.slider('Window overlap (weeks)', 0, window - 1, min(78, window - 1))
    try:
        result = filling_spectrogram(series, window_length=window, overlap=overlap)
        st.pyplot(result.figure)
        plt.close(result.figure)
        st.caption(f'{result.summary["windows"]} windows. Frequency resolution: '
                   f'{result.summary["frequency_resolution_per_year"]:.2f} cycles per year.')
    except ValueError as error:
        st.warning(str(error))
