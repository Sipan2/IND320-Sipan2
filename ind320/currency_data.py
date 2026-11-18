"""Daily NOK exchange rates from Norges Bank."""

from io import StringIO

import pandas as pd
from urllib.parse import urlencode
from urllib.request import urlopen


def download_exchange_rates(start, end):
    """Return observed NOK per EUR and NOK per USD, indexed by publication date."""
    start_date = pd.Timestamp(start).date()
    end_date = pd.Timestamp(end).date()
    if start_date > end_date:
        raise ValueError("The start date must come before or match the end date.")

    query = urlencode({
        "format": "csv",
        "locale": "en",
        "startPeriod": start_date.isoformat(),
        "endPeriod": end_date.isoformat(),
    })
    url = f"https://data.norges-bank.no/api/data/EXR/B.EUR+USD.NOK.SP?{query}"
    with urlopen(url, timeout=30) as response:
        contents = response.read().decode("utf-8-sig")

    observations = pd.read_csv(StringIO(contents), sep=None, engine="python")
    observations["TIME_PERIOD"] = pd.to_datetime(observations["TIME_PERIOD"])
    observations["OBS_VALUE"] = pd.to_numeric(observations["OBS_VALUE"], errors="raise")
    rates = observations.pivot(index="TIME_PERIOD", columns="BASE_CUR", values="OBS_VALUE")
    return rates.reindex(columns=["EUR", "USD"]).sort_index().rename_axis(index="Date", columns=None)
