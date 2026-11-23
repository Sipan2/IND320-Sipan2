# IND320: Reservoirs, weather and forecasting

One Streamlit app brings together Parts 1–4: Norwegian reservoir levels, electricity transfers, weather analysis and weekly reservoir forecasts. Each part has its own notebook and report below.

**[Open the app](https://ind320-sipan2.streamlit.app/)** · [Technical guide](docs/PROJECT_GUIDE.md) · [Database setup](docs/LOCAL_SETUP.txt)

## Project parts

| Part | Notebook | Report | Recording |
| --- | --- | --- | --- |
| 1. Dashboard basics | [Part 1](notebooks/part1.ipynb) | [PDF](reports/part1.pdf) | [Download video](https://github.com/Sipan2/IND320-Sipan2/raw/refs/heads/main/screencasts/IND320-Part-1-screencast.mp4) |
| 2. Data sources | [Part 2](notebooks/part2.ipynb) | [PDF](reports/part2.pdf) | [Download video](https://github.com/Sipan2/IND320-Sipan2/raw/refs/heads/main/screencasts/IND320-Part-2-screencast.mp4) |
| 3. Data quality | [Part 3](notebooks/part3.ipynb) | [PDF](reports/part3.pdf) · [HTML](reports/part3.html) | [Download video](https://github.com/Sipan2/IND320-Sipan2/raw/refs/heads/main/screencasts/IND320-Part-3-screencast.mp4) |
| 4. Machine learning | [Part 4](notebooks/part4.ipynb) | [PDF](reports/part4.pdf) · [HTML](reports/part4.html) | [Download video](https://github.com/Sipan2/IND320-Sipan2/raw/refs/heads/main/screencasts/IND320-Part-4-screencast.mp4) |

The Part 4 notebook, PDF, HTML report and screencast are available. All four screencasts are in `screencasts/`. The higher-bitrate Part 4 video is also available under [GitHub Releases](https://github.com/Sipan2/IND320-Sipan2/releases/tag/part4-screencast).

## Explore the app

| Section | Pages |
| --- | --- |
| Overview | Reservoir map, Data table, Reservoir measurements, Electricity transfers |
| Patterns and data quality | Reservoir patterns, Weather data quality, Weather and filling |
| Prediction | Reservoir forecast |

Select an area on the map to use it in the analysis pages. **Reservoir measurements** contains both the **Measurements** and **Compare areas** tabs. **Weather and filling** explores correlations, while **Reservoir forecast** lets you change the model settings and view an animated forecast.

## Repository layout

| Location | Contents |
| --- | --- |
| `app.py` | Streamlit entry point and navigation |
| `pages/` | Reservoir map, data views, electricity transfers, data quality, weather correlations and forecasts |
| `ind320/` | Shared API access, data processing, analysis and reusable views |
| `notebooks/` | Development and documentation for each project part |
| `data/` | Reproducible region boundaries, sampled coordinates and dated analysis datasets |
| `reports/` | Notebook exports for assessment |
| `screencasts/` | Completed recordings for Parts 1–4 |
| `tests/` | Offline numerical, data-validation and interface regression tests |
| `scripts/` | Manual API and database setup checks |
| `docs/` | Setup instructions, methods and project history |

The app and Part 3 notebook use Parquet for saved tables. The Part 3 PDF and HTML preserve the [original report version](https://github.com/Sipan2/IND320-Sipan2/tree/e4c93adb3473d585cab62e565980af91974cda18), including the file paths used when it was exported.

## Run locally

Use Python 3.12 for the database notebooks. The app and Parts 3–4 notebooks have also been checked with Python 3.13. From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Install `requirements-notebook.txt` for the Part 4 and earlier database notebooks. Use `requirements-part3.txt` for the additional GIS tools used in Part 3. Keep credentials in Streamlit Secrets; the example configuration is in `.streamlit/secrets.toml.example`.

Run the offline checks with:

```sh
python -m unittest discover -s tests
```

## Further details

The [technical guide](docs/PROJECT_GUIDE.md) covers data sources, sampling, analysis assumptions and Git history. Each notebook includes an AI-usage statement and a work log.
