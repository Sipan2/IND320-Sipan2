# IND320: Reservoirs, electricity transfers and data quality

An interactive Streamlit app and three notebooks exploring Norwegian reservoir levels, cross-border electricity transfers and regional weather data.

**[Open the app](https://ind320-sipan2.streamlit.app/)** · [Technical guide](docs/PROJECT_GUIDE.md) · [Database setup](docs/LOCAL_SETUP.txt)

## Project parts

| Part | Notebook | Report | Recording |
| --- | --- | --- | --- |
| 1. Dashboard basics | [Part 1](notebooks/part1.ipynb) | [PDF](reports/reservoirs.pdf) | [Video](screencasts/IND320-Part-1-screencast.mp4) |
| 2. Data sources | [Part 2](notebooks/part2.ipynb) | [PDF](reports/part2.pdf) | [Video](screencasts/IND320-Part-2-screencast.mp4) |
| 3. Data quality | [Part 3](notebooks/part3.ipynb) | [HTML](reports/part3.html) | Pending |

Part 3 and the changes made after Part 2 peer feedback are developed on `part3-data-quality` and merged into `main` for the public app. The Part 3 screencast is still pending.

## Repository layout

| Location | Contents |
| --- | --- |
| `app.py` | Streamlit entry point and navigation |
| `pages/` | Home, tables, plots, electricity transfers and the two data-quality pages |
| `ind320/` | Shared API access, data processing, analysis and reusable views |
| `notebooks/` | Development and documentation for each project part |
| `data/` | Reproducible region boundaries, sampled coordinates and dated analysis datasets |
| `reports/` | Notebook exports for assessment |
| `screencasts/` | Recordings and the Part 3 recording outline |
| `tests/` | Offline numerical, data-validation and interface regression tests |
| `scripts/` | Manual API and database setup checks |
| `docs/` | Setup instructions, methods and project history |

## Run locally

Use Python 3.12 for the database notebooks. The app and Part 3 notebook have also been checked with Python 3.13. From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Install `requirements-part3.txt` for the Part 3 notebook, or `requirements-notebook.txt` for the earlier database notebooks. Keep credentials in Streamlit Secrets; the example configuration is in `.streamlit/secrets.toml.example`.

Run the offline checks with:

```sh
python -m unittest discover -s tests
```

## Changes following peer feedback

Reports and recordings have their own folders. Shared Python modules, tests, setup scripts and documentation are grouped by purpose. The reservoir comparison is now under **Plots → Compare areas**, alongside **Measurements**, with shared area and interval filters.

The [technical guide](docs/PROJECT_GUIDE.md) covers data sources, sampling, analysis assumptions and Git history. Each notebook includes an AI-usage statement and a work log.
