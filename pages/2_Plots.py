import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
import streamlit as st
from data_utils import load_data, select_area, MEASUREMENTS, UNITS

st.set_page_config(page_title="Plots | IND320", layout="wide")
st.title("Plots")
data, area = select_area(load_data())
column = st.selectbox("Column", ["All measurement columns"] + list(data.columns))

# Two handles select a range. Both start at the first month.
months = data["date"].dt.strftime("%Y-%m").drop_duplicates().tolist()
start, end = st.select_slider("Months", options=months, value=(months[0], months[0]))
month_values = data["date"].dt.strftime("%Y-%m")
selected = data.loc[month_values.between(start, end)]
st.caption(f"{len(selected)} weekly observations · area {area} · {start} to {end}")

if column == "All measurement columns":
    # Use the full series for the area as a fixed reference for min-max scaling.
    # This keeps the scale fixed when the month slider changes.
    minimum = data[MEASUREMENTS].min()
    span = data[MEASUREMENTS].max() - minimum
    scaled = (selected[MEASUREMENTS] - minimum) / span.replace(0, 1)
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for name, style in zip(MEASUREMENTS, ["-", "--", ":", "-.", "-"]):
        ax.plot(selected["date"], scaled[name], marker="o" if len(selected) <= 30 else None, markersize=4,
                linestyle=style, linewidth=1.5, label=name.replace("_", " ").capitalize())
    ax.set_ylabel("Min-max scaled value (0-1)")
    ax.set_title(f"Measurements together - {area}")
    ax.legend(fontsize=11, loc="upper center", bbox_to_anchor=(0.5, -0.23), ncol=2, frameon=False)
    st.info("Series are scaled to 0-1 using the full period for the selected area. "
            "This shows relative changes, not absolute values. Constant columns are shown as 0.")
elif column in ["date", "next_publication_date", "area_type"]:
    # Show dates and text in a table because a numeric chart would be misleading.
    st.info("This is a date or text column. Its values are shown in the table below.")
    st.dataframe(selected[list(dict.fromkeys(["date", column]))], hide_index=True)
    st.stop()
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
