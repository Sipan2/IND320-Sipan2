"""Read NVE data without Streamlit, so the notebook can use it too."""
import gzip
import json
from urllib.request import Request, urlopen
import pandas as pd

BASE_URL = 'https://biapi.nve.no/magasinstatistikk/api/Magasinstatistikk/'
COLUMN_NAMES = {
    'dato_Id': 'date', 'omrType': 'area_type', 'omrnr': 'area_number',
    'iso_aar': 'iso_year', 'iso_uke': 'iso_week', 'fyllingsgrad': 'filling_ratio',
    'kapasitet_TWh': 'capacity_twh', 'fylling_TWh': 'stored_energy_twh',
    'neste_Publiseringsdato': 'next_publication_date',
    'fyllingsgrad_forrige_uke': 'previous_week_filling_ratio',
    'endring_fyllingsgrad': 'weekly_filling_ratio_change',
}


def _read_json(url, timeout):
    # NVE serves the same JSON compressed, reducing the initial transfer size.
    request = Request(url, headers={"Accept-Encoding": "gzip"})
    with urlopen(request, timeout=timeout) as response:
        payload = response.read()
        if response.headers.get("Content-Encoding", "").lower() == "gzip":
            payload = gzip.decompress(payload)
    return json.loads(payload)


def fetch_reservoirs():
    # This endpoint returns all observations; it has no documented date parameters.
    data = pd.DataFrame(_read_json(BASE_URL + 'HentOffentligData', timeout=60)).rename(columns=COLUMN_NAMES)
    data['date'] = pd.to_datetime(data['date'])
    return data.sort_values(['area_type', 'area_number', 'date']).reset_index(drop=True)


def fetch_areas():
    groups = _read_json(BASE_URL + 'HentOmr%C3%A5der', timeout=30)
    return pd.DataFrame([area for group in groups for areas in group.values() for area in areas])
