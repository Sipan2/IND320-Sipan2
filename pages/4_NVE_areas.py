from urllib.error import URLError
import altair as alt
import streamlit as st
from data_utils import load_data, load_areas, reservoir_controls

st.title('Reservoir filling by area')
data = load_data()
selected, area_type = reservoir_controls(data)
areas = data.loc[data.area_type == area_type]
start, end = selected.date.min(), selected.date.max()
if selected.empty:
    st.info('There are no weekly observations in this interval. Select a wider range.')
else:
    selected['Area'] = selected.area_type + ' ' + selected.area_number.astype(str)
    selected['Filling level (%)'] = selected.filling_ratio * 100
    chart = alt.Chart(selected).mark_line(point=len(selected) < 40).encode(
        x=alt.X('date:T', title='Observation date'),
        y=alt.Y('Filling level (%):Q', scale=alt.Scale(zero=True)),
        color=alt.Color('Area:N', legend=alt.Legend(orient='bottom', title=None)),
        tooltip=[alt.Tooltip('date:T', title='Date'), 'Area:N',
                 alt.Tooltip('Filling level (%):Q', format='.1f')],
    ).properties(height=410, title=f'Reservoir filling levels - {area_type}')
    st.altair_chart(chart, width='stretch')
    st.caption(f'{len(selected):,} observations · {start:%d %b %Y} to {end:%d %b %Y}')
with st.expander('Areas and data source'):
    st.write('EL identifies electricity price areas, NO 0 covers Norway, and VASS identifies watercourse areas. '
             'These groups have different boundaries, so matching numbers do not mean matching regions.')
    try:
        metadata = load_areas()
        metadata = metadata.loc[metadata.omrType == area_type]
        st.dataframe(metadata[['navn', 'beskrivelse']].rename(columns={'navn': 'Area', 'beskrivelse': 'NVE description (Norwegian)'}), hide_index=True)
        missing = set(metadata.omrnr) - set(areas.area_number)
        if missing:
            st.caption('The area catalogue also lists ' + ', '.join(f'{area_type} {n}' for n in sorted(missing)) + ', but the observations endpoint returned no data for these areas.')
    except (URLError, TimeoutError, ValueError, KeyError):
        st.caption('Area descriptions are temporarily unavailable.')
    st.markdown('[NVE reservoir statistics](https://www.nve.no/energi/analyser-og-statistikk/magasinstatistikk/) · '
                '[API documentation](https://biapi.nve.no/magasinstatistikk/swagger/index.html)')
    st.write('NVE returns the full series. The slider selects the interval shown and included in your download; '
             'it does not limit the API response. Responses are cached for one hour.')
