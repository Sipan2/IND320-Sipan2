from urllib.error import URLError
import pandas as pd
import streamlit as st
from ind320.nve_data import fetch_reservoirs, fetch_areas

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


def reservoir_controls(data):
    """Use the same area type and interval on every reservoir page."""
    if data.empty:
        st.info('No reservoir observations are available. Please try again later.')
        st.stop()
    # Non-widget keys preserve the choices when Streamlit changes pages.
    types = ['EL', 'NO', 'VASS']
    area_type = st.radio('Area type', types,
                        index=types.index(st.session_state.get('nve_type', 'EL')),
                        horizontal=True)
    st.session_state['nve_type'] = area_type
    months = data['date'].dt.strftime('%Y-%m').drop_duplicates().sort_values().tolist()
    saved = st.session_state.get('nve_interval', (months[-min(24, len(months))], months[-1]))
    if any(month not in months for month in saved):
        saved = (months[0], months[-1])
    start, end = st.select_slider('Data and download interval', options=months, value=saved)
    st.session_state['nve_interval'] = (start, end)
    selected = data.loc[data.area_type.eq(area_type) &
                        data.date.dt.strftime('%Y-%m').between(start, end)].copy()
    st.caption('NVE supplies the complete series without date-filter parameters. '
               'This interval selects the data displayed and included in the CSV download.')
    st.download_button('Download selected data as CSV', selected.to_csv(index=False).encode('utf-8'),
                       file_name=f'nve_{area_type}_{start}_{end}.csv', mime='text/csv')
    if selected.empty:
        st.info('No observations in this interval. Select a wider range.')
        st.stop()
    return selected, area_type
