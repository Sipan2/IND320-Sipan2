"""Match complete local calendar weeks to NVE's Sunday observation dates."""
import pandas as pd


def weekly_weather(frame):
    hourly = frame.copy()
    hourly.index = pd.to_datetime(hourly.index, utc=True).tz_convert("Europe/Oslo")
    weekly = hourly.resample("W-SUN").agg({"precipitation": "sum", "temperature_2m": "mean"})
    for day in weekly.index:
        start = day - pd.DateOffset(days=6)
        end = day + pd.DateOffset(days=1)
        expected = int((end - start).total_seconds() / 3600)
        observations = hourly.loc[(hourly.index >= start) & (hourly.index < end)]
        weekly.loc[day, observations[weekly.columns].count().ne(expected)] = float("nan")
    weekly.index = weekly.index.tz_localize(None)
    return weekly


def sliding_correlation(filling, weather, lag, window):
    aligned = pd.concat([filling.rename("Filling"), weather.rename("Weather")], axis=1).asfreq("W-SUN")
    return aligned.Filling.rolling(window).corr(aligned.Weather.shift(lag)).dropna()
