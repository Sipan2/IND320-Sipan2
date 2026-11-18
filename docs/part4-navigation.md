# IND320 Part 4 — Navigation sketch

Draft for the notebook, drawn before changing the app code.

| Page | What it shows | Controls |
| --- | --- | --- |
| Overview | Interactive reservoir area map and links to the analyses | Area type, map colouring, date range and area selection |
| Data and comparison | Reservoir, electricity, weather and exchange rates | Shared area and dates where relevant, with local series selectors |
| Weather and reservoir patterns | SATV, LOF, seasonality and sliding window correlation | Weather variable, lag and window length as applicable |
| Reservoir forecast | Observed and forecast filling using an animated Plotly chart | Shared area and dates, training length, forecast horizon and model inputs |

The map stores the selected area and date range in session state. The analysis pages reuse these selections where relevant. Forecast controls use the same date range as the map, while lag and window settings apply only to the correlation view.
