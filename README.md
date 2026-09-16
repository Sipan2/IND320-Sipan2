# IND320 - Reservoirs

Part 1 of the IND320 project. The notebook explores the CSV data, and the Streamlit app shows a data table and interactive plots.

## Run locally

Use Python 3.12 or newer. Create a virtual environment and install the packages:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open `reservoirs.ipynb` in VS Code or Jupyter and select the same environment as the kernel. Run all cells from the top.

## Files

- `app.py`: home page; `pages/`: the other three pages.
- `data_utils.py`: caching, column names and area selection.
- `data/reservoirs.csv`: original local CSV file.
- `reservoirs.ipynb`: analysis, AI statement and work log.
- `reservoirs.pdf`: PDF export of the executed English notebook.
- `screencast.md`: outline for a five-minute demonstration.

## Analysis choices

The CSV file has nine combinations of area type and area number. Areas are kept separate and dates are sorted before plotting. The first month is January 1995, the earliest calendar month in the dataset. Values are not interpolated or aggregated by month.

The comparison plot uses min-max scaling over the full period for the selected area. Constant columns are shown as 0. Dates and area codes are kept out of the measurement comparison but plotted separately in the notebook. The app table has one row per original column, with small charts for numeric columns.

## Data source

[IND320 / D2Dbook / reservoirs.csv](https://github.com/khliland/IND320/blob/main/D2Dbook/data/reservoirs.csv), downloaded on 16 September 2026.

## Submission status

All eight notebook code cells have been run successfully, with outputs saved. All four English app pages passed local tests, including column selection and the full month range. The PDF includes the executed notebook and plots.

The work log is within the required 300-500 words. The app is published on Streamlit Community Cloud. The screencast will be recorded separately.

The project was developed with help from Codex. See the AI statement in the notebook.

## Publication

GitHub: [Sipan2/IND320-Sipan2](https://github.com/Sipan2/IND320-Sipan2).

For Streamlit Community Cloud, use branch `main`, entry file `app.py` and Python 3.12 or newer. App: [ind320-sipan2.streamlit.app](https://ind320-sipan2.streamlit.app/).
