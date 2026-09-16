from pathlib import Path
import pandas as pd
import streamlit as st

# Use the same English names as in the notebook.
COLUMN_NAMES = {
    "dato_Id": "date", "omrType": "area_type", "omrnr": "area_number",
    "iso_aar": "iso_year", "iso_uke": "iso_week", "fyllingsgrad": "filling_ratio",
    "kapasitet_TWh": "capacity_twh", "fylling_TWh": "stored_energy_twh",
    "neste_Publiseringsdato": "next_publication_date",
    "fyllingsgrad_forrige_uke": "previous_week_filling_ratio",
    "endring_fyllingsgrad": "weekly_filling_ratio_change",
}
MEASUREMENTS = ["filling_ratio", "capacity_twh", "stored_energy_twh",
                "previous_week_filling_ratio", "weekly_filling_ratio_change"]
UNITS = {"filling_ratio": "Fraction", "capacity_twh": "TWh", "stored_energy_twh": "TWh",
         "previous_week_filling_ratio": "Fraction", "weekly_filling_ratio_change": "Change in fraction"}

@st.cache_data
def load_data():
    # Caching avoids reading the CSV file again for each menu selection.
    path = Path(__file__).parent / "data" / "reservoirs.csv"
    data = pd.read_csv(path, parse_dates=["dato_Id"])
    return data.rename(columns=COLUMN_NAMES).sort_values("date")


def select_area(data):
    # Use both the area type and number to identify a series.
    areas = data[["area_type", "area_number"]].drop_duplicates()
    options = list(areas.itertuples(index=False, name=None))
    options = sorted(options, key=lambda area: (area != ("NO", 0), area))
    area = st.selectbox("Area", options, format_func=lambda a: f"{a[0]}, {a[1]}")
    selected = data.loc[(data["area_type"] == area[0]) & (data["area_number"] == area[1])]
    return selected, f"{area[0]}, {area[1]}"

