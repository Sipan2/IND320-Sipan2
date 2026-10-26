# IND320 - Reservoirs and electricity transfers

Part 3 adds a complete NO3 ERA5 weather dataset for 2024, precipitation SPC and temperature LOF analyses, and STL/spectrogram views of reservoir filling. Development is on `part3-data-quality`; the public app still runs the Part 2 version. VASS weather selections use the assignment’s three administrative region unions.

Part 2 reads reservoir observations from NVE and physical electricity flows from ENTSO-E. The transfer dataset covers October 2024 to September 2026 for nine international connections in both directions. Spark writes 1,025,076 intervals to Cassandra, reads them back and prepares 315,360 hourly observations. All monthly coverage checks passed, energy totals match, and the MongoDB upload was verified by reading back the record count. The Streamlit app uses a separate read-only database account.

## Run locally

Use Python 3.12. From the project folder:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

For Part 1 and Part 2 notebooks, install `requirements-notebook.txt`. For Part 3, install `requirements-part3.txt`, which also includes GIS tools, and select that Python 3.12 environment in VS Code. The separate Part 3 checkout uses `.venv-part3`. See `LOCAL_SETUP.txt` for the earlier Docker and database tests.

## Files

PDF exports are stored in `reports/`, and original recordings in `screencasts/`, following the Part 2 feedback. Embedded playback links below are unchanged.

- `app.py` defines navigation; `pages/` contains all seven pages, including Home.
- `nve_data.py` reads the API; `data_utils.py` caches results and selects areas.
- `notebooks/part1.ipynb` preserves the Part 1 analysis and uses the original CSV from a fixed Git commit.
- `notebooks/part2.ipynb` contains the NVE and ENTSO-E analyses and the executed Spark/Cassandra processing. It includes the verified MongoDB record count, AI statement and work log.
- `download_entsoe.py` retrieves the XML; `transfer_data.py` parses intervals and preserves gaps.
- `prepare_transfers.py` checks monthly coverage; `transfer_pipeline.py` runs Spark/Cassandra and uploads the curated records to MongoDB.
- `test_transfer_data.py` checks compressed intervals, missing measurements and invalid responses.
- `test_spark_cassandra.py` writes and reads a small NVE sample through the local database.
- `test_mongodb.py` tests Atlas using that sample and a hidden password prompt.
- `reports/part2.pdf` is the Part 2 notebook export.
- `reports/reservoirs.pdf` and the Part 1 screencast below preserve the previous submission.
- `screencasts/IND320-Part-2-screencast.mp4` is the completed Part 2 walkthrough (4 minutes 44 seconds).
- `notebooks/part3.ipynb` contains executed sampling checks, four analyses, numerical tests, a factual work log and AI attribution.
- `reports/part3.html` is the HTML export of that executed notebook, with five embedded figures. Deployment and submission status are stated explicitly.
- `region_data.py` downloads Atlas boundaries, exports shapefiles and samples locations in an equal-area projection.
- `era5_region.py` downloads and caches ERA5 cells, retaining the weights of all 1,000 original sample locations.
- `weather_data.py` provides the initial direct point-download function used for the pilot.
- `quality_analysis.py` provides shared numerical analysis and plotting functions; `quality_ui.py` provides app controls.
- `data/regions/` contains source boundaries, locally exported shapefiles, sampled coordinates and provenance.
- `data/weather/` contains the verified NO3 hourly means, source manifest and analysis results. Raw responses remain in the ignored `weather_cache/` directory.
- `data/reservoirs/` contains the dated NVE snapshot used for reproducible notebook analyses. The app reservoir pages still fetch NVE directly.

## Part 3 weather and quality analyses

Run `python region_data.py` to rebuild the spatial samples. Run `python era5_region.py` to retrieve the NO3 2024 series. Complete cached responses are reused. Downloads stop if the provider returns a rate-limit response or the conservative local API budget is exhausted.

The regional mean uses nearest ERA5 cells with elevation downscaling disabled. The 1,000 NO3 points occupy 236 cells; each cell retains its original sample weight. All 8,784 hourly means have full spatial coverage. These are grid-scale reanalysis estimates rather than independent station observations.

Weather data are from [Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api), using [Copernicus ERA5](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels), under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Regional means and analyses are derived products.

The Canvas assignment describes EAST=RS+RØ, WEST=RV and NORTH=RM+RN. These polygons have been dissolved and sampled. The coursework mapping is VASS1=EAST, VASS2=WEST and VASS3=NORTH, implemented in `area_mapping.py`. This is the assignment’s administrative weather approximation, not a claim of exact catchment boundaries. The four-code NVE catalogue is preserved separately. The weather app supports electricity, national and all three observed VASS selections. The national sampler uses the union of the electricity-area land polygons; its weather dataset is fetched on demand and has not yet been downloaded in full.

The DCT/SPC flags and LOF anomalies are descriptive statistical results, not confirmed errors. Parameter changes affect the results. See the notebook for feature choices, limitations and exact settings.

Run `python -m unittest test_quality_analysis test_era5_region` for the numerical checks. The two new app pages have also been tested with Streamlit AppTest, including changed parameter values and all three VASS selections.

## Reservoir data

Dates identify observations. Area codes, ISO weeks and publication dates are metadata, not measurements. The combined measurement plot excludes constant columns and scales each changing series to 0-1 using the complete series for that area.

The reservoir pages share area-type radio buttons and an interval slider. The slider controls the plots, area sparklines and CSV download. The API has no documented date-filter parameters, so the app caches the full response before selecting the interval. Area descriptions come from NVE's area catalogue. The catalogue lists VASS 4, but the observations response currently contains VASS 1-3 only.

[NVE statistics](https://www.nve.no/energi/analyser-og-statistikk/magasinstatistikk/) · [NVE API](https://biapi.nve.no/magasinstatistikk/swagger/index.html)

The electricity transfer page uses multi-select month pills. Any set of months can be shown, with gaps between unselected months. Import and export can be selected separately.

## Credentials

Keep passwords and API tokens outside notebooks, outputs and Git. For Streamlit, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`, or enter the settings in Streamlit Cloud. Use a read-only database user for the deployed app. The secrets file is ignored by Git.

## Project links

[GitHub repository](https://github.com/Sipan2/IND320-Sipan2) · [Published app](https://ind320-sipan2.streamlit.app/)

The project was developed with help from Codex. The notebooks describe AI usage.

## Part 2 screencast

The walkthrough demonstrates the app and explains the notebook and database code. Duration: 4 minutes 44 seconds.

https://github.com/user-attachments/assets/8bfc2051-970f-4d30-b1ec-d62feb8dc4bb

[Download the original video](screencasts/IND320-Part-2-screencast.mp4)

## Screencast

Part 1 walkthrough:

https://github.com/user-attachments/assets/f3a0cd7e-b194-4844-8d4b-863c9c6fa026

## Branch history

Part 2 was developed on `part2-data-sources`. Its commits were incorporated into `main` by fast-forward before submission, so the original history contains no merge commit. Following the clarification published on 21 October 2026, this documentation update is merged from `part2-data-sources` with an explicit merge commit. The original commits and dates are preserved.
