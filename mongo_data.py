"""Read curated electricity transfers without exposing connection details."""
import pandas as pd
import streamlit as st
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from streamlit.errors import StreamlitSecretNotFoundError


@st.cache_resource
def get_client():
    # Add these settings locally or in Streamlit Cloud, never in GitHub.
    settings = st.secrets['mongodb']
    return MongoClient(settings['uri'], username=settings['username'],
                       password=settings['password'], serverSelectionTimeoutMS=10000)


@st.cache_data(ttl=600)
def fetch_transfers():
    client = get_client()
    client.admin.command('ping')
    records = list(client['ind320']['transfers'].find({}, {'_id': 0}))
    if not records:
        return pd.DataFrame()
    data = pd.DataFrame(records)
    required = {'connection', 'direction', 'start_utc', 'end_utc', 'power_mw', 'energy_mwh'}
    if not required.issubset(data.columns):
        raise ValueError('The transfer collection does not have the expected fields.')
    data['start_utc'] = pd.to_datetime(data['start_utc'], utc=True)
    data['end_utc'] = pd.to_datetime(data['end_utc'], utc=True)
    return data.sort_values('start_utc')


def load_transfers():
    try:
        return fetch_transfers()
    except (StreamlitSecretNotFoundError, KeyError):
        st.info('Electricity transfer data is not connected yet.')
    except (PyMongoError, ValueError):
        # Connection exceptions can contain server details; do not display them.
        st.error('Electricity transfer data could not be loaded. Please try again later.')
    st.stop()
