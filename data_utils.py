from urllib.error import URLError
import pandas as pd
import streamlit as st
from nve_data import fetch_reservoirs, fetch_areas

MEASUREMENTS = ['filling_ratio', 'capacity_twh', 'stored_energy_twh',
                'previous_week_filling_ratio', 'weekly_filling_ratio_change']
UNITS = {'filling_ratio': 'Fraction', 'capacity_twh': 'TWh', 'stored_energy_twh': 'TWh',
         'previous_week_filling_ratio': 'Fraction', 'weekly_filling_ratio_change': 'Change in fraction'}


@st.cache_data(ttl=3600, show_spinner='Loading reservoir data from NVE...')
def cached_reservoirs():
    # Reuse the API response across pages and refresh it after an hour.
    return fetch_reservoirs()


def load_data():
    try:
        return cached_reservoirs()
    except (URLError, TimeoutError, ValueError, KeyError):
        st.error('NVE data could not be loaded. Please try again later.')
        st.stop()


@st.cache_data(ttl=86400)
def load_areas():
    return fetch_areas()


def select_area(data):
    # Both fields are needed: EL 1 and VASS 1 describe different areas.
    options = list(data[['area_type', 'area_number']].drop_duplicates().itertuples(index=False, name=None))
    options = sorted(options, key=lambda area: (area != ('NO', 0), area))
    area = st.selectbox('Area', options, format_func=lambda a: f'{a[0]}, {a[1]}')
    selected = data.loc[(data.area_type == area[0]) & (data.area_number == area[1])]
    return selected, f'{area[0]}, {area[1]}'
