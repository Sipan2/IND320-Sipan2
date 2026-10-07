# IND320 - Reservoirs and electricity transfers

Part 2 is in progress on `part2-data-sources`. The app now reads reservoir observations directly from NVE. ENTSO-E access, the complete transfer analysis and MongoDB deployment are still pending. The published app on `main` remains the Part 1 version.

## Run locally

Use Python 3.12. From the project folder:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

For the notebooks, install `requirements-notebook.txt` instead and select the same Python environment in VS Code. This Mac already has an environment one folder above the project, at `../.venv`. See `LOCAL_SETUP.txt` for the Docker and database tests.

## Files

- `app.py` defines navigation; `pages/` contains all five pages, including Home.
- `nve_data.py` reads the API; `data_utils.py` caches results and selects areas.
- `notebooks/part1.ipynb` preserves the Part 1 analysis and uses the original CSV from a fixed Git commit.
- `notebooks/part2.ipynb` contains the current NVE analysis and Spark/Cassandra setup check.
- `test_spark_cassandra.py` writes and reads a small NVE sample through the local database.
- `test_mongodb.py` tests Atlas using that sample and a hidden password prompt.
- `reservoirs.pdf` and the screencast below belong to Part 1.

## Reservoir data

Dates identify observations. Area codes, ISO weeks and publication dates are metadata, not measurements. The combined measurement plot excludes constant columns and scales each changing series to 0-1 using the complete series for that area.

On NVE areas, the interval slider controls the chart and CSV download. The API has no documented date-filter parameters, so the app caches the full response before selecting the interval. Area descriptions come from NVE's area catalogue. The catalogue lists VASS 4, but the observations response currently contains VASS 1-3 only.

[NVE statistics](https://www.nve.no/energi/analyser-og-statistikk/magasinstatistikk/) · [NVE API](https://biapi.nve.no/magasinstatistikk/swagger/index.html)

## Credentials

Keep passwords and API tokens outside notebooks, outputs and Git. For Streamlit, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, or enter the settings in Streamlit Cloud. Use a read-only database user for the deployed app. The secrets file is ignored by Git.

## Project links

[GitHub repository](https://github.com/Sipan2/IND320-Sipan2) · [Published app](https://ind320-sipan2.streamlit.app/)

The project was developed with help from Codex. The notebooks describe AI usage.

## Screencast

Part 1 walkthrough:

https://github.com/user-attachments/assets/f3a0cd7e-b194-4844-8d4b-863c9c6fa026
