"""Compare weekly reservoir filling levels for every area of the selected type."""
import pandas as pd
import streamlit as st
from data_utils import load_data, reservoir_controls

st.title('Data table')
data, area_type = reservoir_controls(load_data())
st.subheader(f'Reservoir filling levels - {area_type}')
st.write('One row per area. Each small chart shows weekly filling levels in the selected interval.')
# Align every series to the same dates, preserving missing observations as gaps.
dates = sorted(data.date.unique())
rows = []
for number, group in data.groupby('area_number'):
    levels = group.set_index('date')['filling_ratio'].reindex(dates) * 100
    available = levels.dropna()
    rows.append({'Area': f'{area_type} {number}',
                 'First (%)': available.iloc[0] if not available.empty else None,
                 'Last (%)': available.iloc[-1] if not available.empty else None,
                 'Filling level (%)': [None if pd.isna(v) else float(v) for v in levels]})
st.dataframe(pd.DataFrame(rows), hide_index=True, width='stretch', column_config={
    'Filling level (%)': st.column_config.LineChartColumn('Filling level (%)', y_min=0, y_max=100, width='large'),
    'First (%)': st.column_config.NumberColumn(format='%.1f'),
    'Last (%)': st.column_config.NumberColumn(format='%.1f'),
})
st.caption('All small charts use the same dates and a 0-100% scale. Missing observations remain gaps.')
with st.expander('Weekly observations'):
    st.dataframe(data, hide_index=True, width='stretch')
