import pandas as pd
import streamlit as st
from data_utils import load_data, select_area

st.set_page_config(page_title="Data table | IND320", layout="wide")
st.title("Data table")
data, area = select_area(load_data())

# The first month is the earliest calendar month after sorting.
month = data["date"].dt.to_period("M").min()
first_month = data.loc[data["date"].dt.to_period("M") == month]
st.subheader(f"First month: {month} · area {area}")
st.write("One row per CSV column. The small charts follow the weekly measurements.")
rows = []
for column in data.columns:
    values = first_month[column]
    numeric = pd.api.types.is_numeric_dtype(values)
    rows.append({"Column": column, "First value": str(values.iloc[0]),
                 "Last value": str(values.iloc[-1]),
                 "First month": values.tolist() if numeric else None})

# LineChartColumn needs a list of numbers in each cell.
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch",
    column_config={"First month": st.column_config.LineChartColumn("First month", width="large")})
st.caption("Dates and text have no small chart. Area codes, years and weeks are metadata, not measurements. "
           "Each chart has its own scale, so their heights cannot be compared directly.")
st.subheader("Raw data for the first month")
st.dataframe(first_month, hide_index=True, width="stretch")
with st.expander("Show all rows for the selected area"):
    st.dataframe(data, hide_index=True, width="stretch")
