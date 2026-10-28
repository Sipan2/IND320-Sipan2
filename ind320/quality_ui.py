"""Shared controls and sources for the two data-quality pages."""
from pathlib import Path

import pandas as pd
import streamlit as st

from ind320.area_mapping import weather_region, PRECIPITATION_MEMBERS
from ind320.data_utils import load_data
from ind320.era5_region import regional_weather, QuotaBudgetReached

ROOT = Path(__file__).resolve().parents[1]


def area_control(data, prefix):
    """Reuse the shared family choice, with a local identifier on each page."""
    types = ['EL', 'NO', 'VASS']
    previous = st.session_state.get('nve_type', 'EL')
    family = st.radio('Area type', types, index=types.index(previous), horizontal=True, key=prefix + '_family')
    st.session_state['nve_type'] = family
    numbers = sorted(data.loc[data.area_type.eq(family), 'area_number'].unique().tolist())
    default = numbers.index(3) if family == 'EL' and 3 in numbers else 0
    number = st.selectbox('Area', numbers, index=default,
                          format_func=lambda n: f'{family} {n}', key=prefix + '_area')
    return family, number


def filling_control():
    data = load_data()
    family, number = area_control(data, 'quality_filling')
    frame = data.loc[data.area_type.eq(family) & data.area_number.eq(number)].sort_values('date')
    st.caption(f'NVE observations for {family} {number}: {frame.date.min():%d %b %Y} to {frame.date.max():%d %b %Y}. '
               'Both analyses use the complete weekly series. Missing observations are not filled automatically.')
    return frame.set_index('date').filling_ratio


def weather_control():
    data = load_data()
    family, number = area_control(data, 'quality_weather')
    region_type, region = weather_region(family, number)
    if family == 'VASS':
        st.caption(f'Assignment weather region: {region.title()} = '
                   f'{" + ".join(PRECIPITATION_MEMBERS[region])}. '
                   'These administrative polygon unions follow the coursework definition; '
                   'they are not exact hydrological catchment boundaries.')
    year = st.number_input('Weather year', min_value=1940, max_value=2025, value=2024, step=1)
    start, end = f'{year}-01-01', f'{year}-12-31'
    path = ROOT / f'data/weather/{region_type}_{region}_{start}_{end}.csv'
    st.caption('Hourly ERA5 precipitation and temperature from Open-Meteo. The regional mean retains equal '
               'weights for 1,000 area-sampled points. Points in the same 0.25° cell share its model series. '
               'Nearest-cell selection is used and elevation downscaling is disabled.')
    if st.button('Fetch selected weather from Open-Meteo', key='quality_fetch_weather'):
        bar = st.progress(0, text='Preparing weather download…')
        try:
            regional_weather(region, start, end, region_type=region_type,
                             progress=lambda done, total: bar.progress(done / total, text=f'Weather cells: {done}/{total}'))
            st.success('The complete regional dataset has been saved.')
        except (QuotaBudgetReached, OSError, ValueError, KeyError) as error:
            st.error(f'Weather download stopped: {error}')
        finally:
            bar.empty()
    if not path.exists():
        st.info('No complete dataset is saved for this selection. Fetch it above; this can take several minutes.')
        return None
    frame = pd.read_csv(path, parse_dates=['time_utc']).set_index('time_utc')
    st.caption(f'Saved complete dataset: {len(frame):,} hours; {int(frame.sample_count.iloc[0]):,} sampled points, '
               f'{int(frame.grid_cell_count.iloc[0]):,} occupied grid cells. This is reanalysis, not station observations.')
    st.markdown('[Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api) · '
                '[Copernicus ERA5](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels) · '
                '[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)')
    return frame
