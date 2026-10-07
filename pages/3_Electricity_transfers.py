import streamlit as st
from mongo_data import load_transfers

st.title('Electricity transfers')
st.write('This page will show transfers into and out of Norway from ENTSO-E, '
         'prepared in the notebook and stored in MongoDB.')
st.info('Under development: ENTSO-E access and the complete data pipeline are still pending.')
with st.expander('Data source and preparation'):
    st.markdown('[ENTSO-E Transparency Platform](https://transparency.entsoe.eu/)')
    st.write('Physical flow data will be stored in Cassandra through Spark. '
             'Selected fields will then be transferred to MongoDB. Energy totals must '
             'account for the duration of each measurement interval.')
    st.caption('The right-hand chart requirements are still marked “Not updated yet” in Canvas, checked on 7 October 2026.')
data = load_transfers()
if data.empty:
    st.info('No curated electricity transfer observations have been uploaded yet.')
    st.stop()
# Do not imply a finished analysis until coverage and units have been checked.
st.dataframe(data.head(20), hide_index=True, width='stretch')
