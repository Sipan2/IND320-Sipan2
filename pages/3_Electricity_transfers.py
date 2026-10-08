"""Explore hourly physical flows retrieved from the curated MongoDB collection."""
import altair as alt
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from mongo_data import load_transfers

st.title('Electricity transfers')
st.write('Physical electricity flows into and out of Norway. Import and export are measured from Norway’s perspective.')
data = load_transfers()
if data.empty:
    st.info('Electricity transfer observations have not been uploaded yet.')
    st.stop()

# Local dates make the year and month selectors match Norwegian calendar periods.
data['local_time'] = data['start_utc'].dt.tz_convert('Europe/Oslo')
left, right = st.columns(2)
with left:
    connection = st.radio('Connection', sorted(data['connection'].unique()))
    selected = data.loc[data['connection'].eq(connection)].copy()
    years = sorted(selected['local_time'].dt.year.unique().tolist())
    year = st.selectbox('Year', years, index=years.index(2025) if 2025 in years else 0)
    annual = selected.loc[selected['local_time'].dt.year.eq(year)]
    totals = annual.groupby('direction')['energy_mwh'].sum().reindex(['import', 'export'], fill_value=0)
    st.subheader(f'{connection}: {year}')
    if totals.sum() > 0:
        fig, ax = plt.subplots(figsize=(5, 4))
        ax.pie(totals, labels=['Import', 'Export'], autopct='%1.1f%%',
               colors=['#2878b5', '#e88a24'], startangle=90,
               wedgeprops={'edgecolor': 'white'})
        ax.set_title('Share of recorded energy')
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info('No positive recorded energy for this selection.')
    st.caption(f"Import: {totals['import'] / 1000:,.1f} GWh. Export: {totals['export'] / 1000:,.1f} GWh.")
    # Report incomplete coverage instead of presenting partial years as full years.
    start = pd.Timestamp(year=year, month=1, day=1, tz='Europe/Oslo')
    end = start + pd.DateOffset(years=1)
    expected_hours = (end - start).total_seconds() / 3600
    if 'observed_hours' in annual:
        coverage = annual.groupby('direction')['observed_hours'].sum().reindex(['import', 'export'], fill_value=0)
        if (coverage < expected_hours - 0.001).any():
            st.warning('This year has incomplete coverage. The pie shows recorded energy only.')
        st.caption('Coverage: ' + ', '.join(f'{direction} {hours / expected_hours:.1%}' for direction, hours in coverage.items()))

with right:
    months = sorted(annual['local_time'].dt.month.unique().tolist())
    month = st.selectbox('Month', months, format_func=lambda m: pd.Timestamp(2000, m, 1).strftime('%B'))
    directions = st.pills('Direction', ['import', 'export'], selection_mode='multi', default=['import', 'export'])
    monthly = annual.loc[annual['local_time'].dt.month.eq(month) & annual['direction'].isin(directions)].copy()
    st.subheader('Hourly physical flow')
    if monthly.empty:
        st.info('Select at least one direction with observations.')
    else:
        # Insert absent hours as NaN so the chart does not join across missing data.
        chart_rows = []
        first = pd.Timestamp(year=year, month=month, day=1, tz='Europe/Oslo').tz_convert('UTC')
        last = (first.tz_convert('Europe/Oslo') + pd.DateOffset(months=1)).tz_convert('UTC')
        hours = pd.date_range(first, last, freq='h', inclusive='left')
        for direction in directions:
            series = monthly.loc[monthly['direction'].eq(direction)].set_index('start_utc')
            series = series.reindex(hours)
            series['direction'] = direction
            series['time'] = hours
            chart_rows.append(series.reset_index(drop=True))
        plot = pd.concat(chart_rows)
        chart = alt.Chart(plot).mark_line(invalid='break-paths-show-domains').encode(
            x=alt.X('time:T', title='Date and time (UTC)', scale=alt.Scale(type='utc')),
            y=alt.Y('power_mw:Q', title='Average power (MW)'),
            color=alt.Color('direction:N', title='Direction',
                            scale=alt.Scale(domain=['import', 'export'], range=['#2878b5', '#e88a24'])),
            tooltip=[alt.Tooltip('time:T', title='UTC'), 'direction:N', alt.Tooltip('power_mw:Q', format='.1f')]
        ).properties(height=340)
        st.altair_chart(chart, width='stretch')
        st.caption('Hours with missing observations remain gaps. Values are hourly averages over the observed intervals.')

with st.expander('Data source and preparation'):
    st.markdown('[ENTSO-E Transparency Platform](https://transparency.entsoe.eu/) supplies physical cross-border flows (A11).')
    st.write('Coverage requested: October 2024 to September 2026. Spark writes the intervals to Cassandra, reads back the relevant fields and prepares hourly observations for MongoDB. Energy is power multiplied by interval duration. The app reads MongoDB with a read-only account.')
