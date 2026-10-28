"""Reusable plots and numerical results for the Part 3 data-quality analyses."""
from dataclasses import dataclass

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.fft import dct, idct
from scipy.signal import spectrogram
from scipy.stats import median_abs_deviation
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.seasonal import STL


@dataclass
class AnalysisResult:
    figure: object
    data: pd.DataFrame
    summary: dict


def regular_series(series, minimum=8):
    """Reject gaps instead of silently inventing observations for a transform."""
    if not isinstance(series, pd.Series) or not isinstance(series.index, pd.DatetimeIndex):
        raise ValueError('Provide a Series with a DatetimeIndex.')
    if len(series) < minimum or series.index.has_duplicates or not series.index.is_monotonic_increasing:
        raise ValueError('The series must have enough distinct, increasing timestamps.')
    values = series.to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError('Missing and infinite observations require an explicit preprocessing decision.')
    steps = np.diff(series.index.asi8)
    if not np.all(steps == steps[0]) or steps[0] <= 0:
        raise ValueError('The analysis requires equally spaced observations.')
    return values, float(steps[0]) / (86400 * 1e9)


def precipitation_spc(series, cutoff_cycles_per_day=1 / 30, deviations=3):
    """Use DCT high-pass residuals to identify unusual precipitation hours.

    The low-frequency reconstruction supplies the moving centre. The median
    and normal-consistent MAD of the full-year residuals supply robust limits.
    These are descriptive flags, not a claim of Gaussian precipitation or an
    independent-process false-alarm probability. Outliers are not removed.
    """
    values, days = regular_series(series)
    if (values < 0).any() or not 0 < cutoff_cycles_per_day < 1 / (2 * days):
        raise ValueError('Use non-negative precipitation and a cut-off below Nyquist.')
    if not np.isfinite(deviations) or deviations <= 0:
        raise ValueError('The number of deviations must be positive.')
    coefficients = dct(values, type=2, norm='ortho')
    # DCT-II index k corresponds to k/(2*N*sample_interval) cycles/day.
    frequencies = np.arange(len(values)) / (2 * len(values) * days)
    low = coefficients.copy()
    low[frequencies >= cutoff_cycles_per_day] = 0
    baseline = idct(low, type=2, norm='ortho')
    residual = values - baseline
    centre = float(np.median(residual))
    scale = float(median_abs_deviation(residual, scale='normal'))
    tolerance = np.finfo(float).eps * max(1, np.abs(values).max()) * 100
    lower = baseline + centre - deviations * scale
    upper = baseline + centre + deviations * scale
    flagged = (values < lower - tolerance) | (values > upper + tolerance)
    table = pd.DataFrame({'precipitation_mm': values, 'lower_mm': lower,
                          'upper_mm': upper, 'outlier': flagged}, index=series.index)
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(series.index, values, color='#2274a5', linewidth=0.7, label='Mean precipitation')
    ax.plot(series.index, lower, color='#64748b', linestyle='--', linewidth=0.8, label='Robust SPC limits')
    ax.plot(series.index, upper, color='#64748b', linestyle='--', linewidth=0.8)
    ax.scatter(series.index[flagged], values[flagged], color='#c74632', s=12, label='Flagged hours', zorder=3)
    ax.set(title='Regional precipitation and robust SPC limits', xlabel='Date (UTC)', ylabel='Precipitation (mm per hour)')
    ax.legend(loc='upper left', bbox_to_anchor=(0, -0.19), ncol=3)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    return AnalysisResult(fig, table, {'observations': len(values), 'outliers': int(flagged.sum()),
                                      'outlier_fraction': float(flagged.mean()), 'robust_sigma_mm': scale,
                                      'cutoff_cycles_per_day': cutoff_cycles_per_day,
                                      'deviations': deviations, 'degenerate_scale': bool(scale <= tolerance)})


def temperature_lof(series, contamination=0.01, neighbours=20):
    """Find locally sparse temperature/change pairs with Local Outlier Factor.

    Features are temperature and the change from the preceding hour. They are
    standardised to prevent their different scales dominating distance. The
    first timestamp has no preceding change and is excluded explicitly. LOF
    describes feature-space neighbours, not automatically a temporal window.
    """
    values, _ = regular_series(series)
    if not 0 < contamination <= 0.5 or not 2 <= neighbours < len(values) - 1:
        raise ValueError('Use contamination in (0, 0.5] and fewer neighbours than feature rows.')
    features = np.column_stack([values[1:], np.diff(values)])
    features = StandardScaler().fit_transform(features)
    model = LocalOutlierFactor(n_neighbors=int(neighbours), contamination=contamination)
    prediction = model.fit_predict(features)
    flagged = np.r_[False, prediction == -1]
    table = pd.DataFrame({'temperature_c': values, 'change_c': np.r_[np.nan, np.diff(values)],
                          'lof_score': np.r_[np.nan, -model.negative_outlier_factor_],
                          'evaluated': np.r_[False, np.ones(len(values) - 1, dtype=bool)],
                          'anomaly': flagged}, index=series.index)
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(series.index, values, color='#2274a5', linewidth=0.7, label='Mean temperature')
    ax.scatter(series.index[flagged], values[flagged], s=16, color='#c74632', label='LOF anomalies', zorder=3)
    ax.set(title='Regional temperature and LOF anomalies', xlabel='Date (UTC)', ylabel='Temperature (°C)')
    ax.legend(loc='upper left', bbox_to_anchor=(0, -0.19), ncol=2)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    return AnalysisResult(fig, table, {'observations': len(values), 'evaluated': len(values) - 1,
                                      'anomalies': int(flagged.sum()), 'requested_fraction': contamination,
                                      'actual_fraction': float(flagged.sum() / (len(values) - 1)),
                                      'neighbours': int(neighbours), 'excluded_initial_rows': 1})


def filling_stl(series, seasonal=13, trend=81, robust=True, period=52):
    """Decompose weekly filling; 52 weeks is an approximation to a calendar year."""
    values, days = regular_series(series, minimum=2 * period)
    if not np.isclose(days, 7):
        raise ValueError('The filling-series defaults require weekly data.')
    if seasonal < 7 or seasonal % 2 != 1 or trend <= period or trend % 2 != 1:
        raise ValueError('Use odd seasonal >= 7 and odd trend > period.')
    if not isinstance(robust, (bool, np.bool_)):
        raise ValueError('robust must be a Boolean.')
    fitted = STL(series, period=int(period), seasonal=int(seasonal), trend=int(trend), robust=bool(robust)).fit()
    table = pd.DataFrame({'observed': values, 'trend': fitted.trend,
                          'seasonal': fitted.seasonal, 'residual': fitted.resid}, index=series.index)
    fig, axes = plt.subplots(4, 1, figsize=(11, 8), sharex=True)
    for ax, column in zip(axes, table):
        ax.plot(table.index, table[column], linewidth=0.8, color='#2274a5')
        ax.set_ylabel(column.capitalize())
        ax.grid(alpha=0.2)
    axes[0].set_title('Reservoir filling: STL decomposition (fraction)')
    axes[-1].set_xlabel('Observation date')
    fig.tight_layout()
    return AnalysisResult(fig, table, {'observations': len(values), 'period_weeks': period,
                                      'seasonal': seasonal, 'trend': trend, 'robust': bool(robust),
                                      'max_reconstruction_error': float(np.max(np.abs(values - table[['trend', 'seasonal', 'residual']].sum(axis=1))))})


def filling_spectrogram(series, window_length=104, overlap=78):
    """Show filling variation by frequency and time, using a Hann window.

    Frequencies are cycles per 365.25-day year. The window is specified in
    weekly observations. A 104-week window resolves annual variation while
    preserving several time windows in the longer NVE record.
    """
    values, days = regular_series(series)
    if not np.isclose(days, 7) or not 8 <= window_length <= len(values):
        raise ValueError('Use weekly data and a window between 8 and the series length.')
    if int(window_length) != window_length or int(overlap) != overlap or not 0 <= overlap < window_length:
        raise ValueError('Use integer window/overlap with 0 <= overlap < window.')
    # The established SciPy spectrogram API is used for this teaching workflow.
    freq, elapsed, density = spectrogram(values, fs=365.25 / days, window='hann',
                                         nperseg=int(window_length), noverlap=int(overlap),
                                         detrend='linear', scaling='density', mode='psd')
    dates = series.index[0] + pd.to_timedelta(elapsed * 365.25, unit='D')
    power_db = 10 * np.log10(np.maximum(density, np.finfo(float).tiny))
    fig, ax = plt.subplots(figsize=(11, 4.5))
    image = ax.pcolormesh(mdates.date2num(dates.to_pydatetime()), freq, power_db, shading='auto', cmap='viridis')
    ax.xaxis_date()
    ax.set(title='Reservoir filling: spectrogram', xlabel='Window centre date', ylabel='Frequency (cycles per year)')
    fig.colorbar(image, ax=ax, label='Power density (dB relative to fraction² per cycle/year)')
    fig.tight_layout()
    table = pd.DataFrame(density.T, index=dates, columns=freq)
    return AnalysisResult(fig, table, {'window_weeks': int(window_length), 'overlap_weeks': int(overlap),
                                      'windows': len(dates), 'frequency_resolution_per_year': float(freq[1] - freq[0])})
