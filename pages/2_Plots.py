import streamlit as st
from ind320.data_utils import load_data, reservoir_controls
from ind320.reservoir_views import measurement_plots, area_comparison

st.title('Reservoir plots')
all_data = load_data()
interval_data, area_type = reservoir_controls(all_data)
measurement_tab, comparison_tab = st.tabs(['Measurements', 'Compare areas'])
with measurement_tab:
    measurement_plots(all_data, interval_data, area_type)
with comparison_tab:
    area_comparison(all_data, interval_data, area_type)
