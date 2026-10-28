import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
import streamlit as st
from ind320.data_utils import select_area, MEASUREMENTS, UNITS

from urllib.error import URLError
import altair as alt
from ind320.data_utils import load_areas


def measurement_plots(all_data, interval_data, area_type):
    selected, area = select_area(interval_data)
    # Retain the full area series as a fixed reference for scaling.
    number = selected.area_number.iloc[0]
    data = all_data.loc[all_data.area_type.eq(area_type) & all_data.area_number.eq(number)]
    column = st.selectbox("Column", ["All measurement columns"] + list(data.columns))
    st.caption(f"{len(selected)} weekly observations · area {area}")

    if column == "All measurement columns":
        # Use the full series for the area as a fixed reference for min-max scaling.
        # This keeps the scale fixed when the month slider changes.
        minimum = data[MEASUREMENTS].min()
        span = data[MEASUREMENTS].max() - minimum
        changing = span[span > 0].index.tolist()
        constant = span[span == 0].index.tolist()
        scaled = (selected[changing] - minimum[changing]) / span[changing]
        fig, ax = plt.subplots(figsize=(11, 5.5))
        for name, style in zip(changing, ["-", "--", ":", "-.", "-"]):
            ax.plot(selected["date"], scaled[name], marker="o" if len(selected) <= 30 else None, markersize=4,
                    linestyle=style, linewidth=1.5, label=name.replace("_", " ").capitalize())
        ax.set_ylabel("Min-max scaled value (0-1)")
        ax.set_title(f"Measurements together - {area}")
        ax.legend(fontsize=11, loc="upper center", bbox_to_anchor=(0.5, -0.23), ncol=2, frameon=False)
        st.info("Series are scaled to 0-1 using the full period for the selected area. "
                "This shows relative changes, not absolute values. Constant columns are excluded because they have no range.")
        if constant:
            st.caption('Constant measurements: ' + ', '.join(name.replace('_', ' ') for name in constant))
    elif column in ["date", "next_publication_date", "area_type"]:
        # Show dates and text in a table because a numeric chart would be misleading.
        st.info("This is a date or text column. Its values are shown in the table below.")
        st.dataframe(selected[list(dict.fromkeys(["date", column]))], hide_index=True)
        return
    else:
        fig, ax = plt.subplots(figsize=(11, 5.5))
        ax.plot(selected["date"], selected[column], marker="o" if len(selected) <= 30 else None, markersize=4, linewidth=1.3)
        ax.set_title(f"{column.replace('_', ' ').capitalize()} - area {area}")
        ax.set_ylabel(UNITS.get(column, "Code / calendar value"))
        if column not in MEASUREMENTS:
            st.caption("This column is metadata. The numbers describe the area or calendar, not reservoir levels.")

    # Limit date labels so both a single month and a long period stay readable.
    locator = mdates.AutoDateLocator(minticks=3, maxticks=7, interval_multiples=False)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
    ax.tick_params(labelsize=11)
    ax.xaxis.label.set_size(12)
    ax.yaxis.label.set_size(12)
    ax.title.set_size(15)
    if column in ["area_number", "iso_year", "iso_week"]:
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        if selected[column].nunique() == 1:
            value = selected[column].iloc[0]
            ax.set_yticks([value])
            ax.set_ylim(value - 0.5, value + 0.5)
    ax.set_xlabel("Date")
    ax.grid(alpha=0.25)
    ax.margins(x=0.02)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def area_comparison(all_data, interval_data, area_type):
    """Compare all observed areas in the selected family and interval."""
    selected = interval_data.copy()
    areas = all_data.loc[all_data.area_type == area_type]
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
