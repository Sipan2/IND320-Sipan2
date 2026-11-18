"""Recursive weekly forecasts for one reservoir area."""
import math

import pandas as pd
from river import linear_model, optim, preprocessing


def forecast_filling(filling, history=260, horizon=12, lags=8, rate=0.01, inputs=None):
    """Predict weekly changes. Future external inputs stay at their last known value."""
    if filling.isna().any() or not filling.map(math.isfinite).all():
        raise ValueError("Training observations must be finite and complete.")
    y = filling.sort_index().tail(history)
    if not isinstance(y.index, pd.DatetimeIndex) or not y.index.to_series().diff().dropna().eq(pd.Timedelta(weeks=1)).all():
        raise ValueError("Select a continuous weekly series.")
    if len(y) < lags + 8 or not 1 <= horizon <= 52 or lags < 1 or rate <= 0:
        raise ValueError("Choose a longer history or fewer lags, and a horizon of 1 to 52 weeks.")
    external = pd.DataFrame(index=y.index) if inputs is None else inputs.reindex(y.index).ffill()
    model = preprocessing.StandardScaler() | linear_model.LinearRegression(optimizer=optim.SGD(rate))

    def features(date, past, predictors):
        angle = 2 * math.pi * date.dayofyear / 365.25
        row = {"season_sin": math.sin(angle), "season_cos": math.cos(angle)}
        row.update({f"lag_{i}": past[-i] for i in range(1, lags + 1)})
        row.update(predictors)
        return row

    past = list(y.iloc[:lags])
    trained = 0
    for pos in range(lags, len(y)):
        # Only inputs available by the previous observation enter the fit.
        known = external.iloc[pos - 1]
        if known.notna().all():
            x = features(y.index[pos], past, known.to_dict())
            model.learn_one(x, float(y.iloc[pos] - past[-1]))
            trained += 1
        past.append(float(y.iloc[pos]))
    if trained < 8 or external.iloc[-1].isna().any():
        raise ValueError("The selected inputs need at least eight overlapping training weeks.")
    dates = pd.date_range(y.index[-1] + pd.Timedelta(weeks=1), periods=horizon, freq="7D")
    for date in dates:
        x = features(date, past, external.iloc[-1].to_dict())
        past.append(min(1.0, max(0.0, past[-1] + model.predict_one(x))))
    return pd.Series(past[-horizon:], index=dates, name="Forecast")
