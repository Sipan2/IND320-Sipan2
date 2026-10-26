"""Numerical checks using known signals and deliberately incomplete inputs."""
import unittest

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from quality_analysis import (precipitation_spc, temperature_lof,
                              filling_stl, filling_spectrogram)


class QualityChecks(unittest.TestCase):
    def tearDown(self):
        plt.close('all')

    def test_spc_flags_injected_spike_and_accepts_constant_series(self):
        rng = np.random.default_rng(320)
        times = pd.date_range('2024-01-01', periods=8784, freq='h', tz='UTC')
        values = 1 + 0.4 * np.cos(np.arange(len(times)) * 2 * np.pi / len(times)) + rng.normal(0, 0.03, len(times))
        values[4000] += 8
        result = precipitation_spc(pd.Series(values, index=times))
        self.assertTrue(result.data.outlier.iloc[4000])
        constant = precipitation_spc(pd.Series(0.0, index=times))
        self.assertEqual(constant.summary['outliers'], 0)

    def test_lof_detects_known_isolated_extreme(self):
        rng = np.random.default_rng(320)
        times = pd.date_range('2024-01-01', periods=2000, freq='h', tz='UTC')
        values = rng.normal(0, 1, len(times))
        values[1000] = 50
        result = temperature_lof(pd.Series(values, index=times))
        self.assertTrue(result.data.anomaly.iloc[1000])
        self.assertFalse(result.data.evaluated.iloc[0])
        self.assertAlmostEqual(result.summary['actual_fraction'], 0.01, delta=0.001)

    def test_stl_reconstructs_and_recovers_known_season(self):
        times = pd.date_range('2014-01-05', periods=520, freq='7D')
        season = 0.2 * np.sin(2 * np.pi * np.arange(520) / 52)
        values = 0.5 + 0.0001 * np.arange(520) + season
        result = filling_stl(pd.Series(values, index=times))
        self.assertLess(result.summary['max_reconstruction_error'], 1e-10)
        self.assertGreater(np.corrcoef(season, result.data.seasonal)[0, 1], 0.99)

    def test_spectrogram_recovers_annual_frequency(self):
        times = pd.date_range('2014-01-05', periods=520, freq='7D')
        values = np.sin(2 * np.pi * np.arange(520) / 52)
        result = filling_spectrogram(pd.Series(values, index=times))
        dominant = float(result.data.mean().idxmax())
        self.assertAlmostEqual(dominant, 365.25 / (7 * 52), delta=0.01)

    def test_missing_dates_and_values_are_not_silently_filled(self):
        series = pd.Series(1.0, index=pd.date_range('2024-01-01', periods=100, freq='h'))
        with self.assertRaises(ValueError):
            precipitation_spc(series.drop(series.index[20]))
        series.iloc[20] = np.nan
        with self.assertRaises(ValueError):
            temperature_lof(series)


if __name__ == '__main__':
    unittest.main()
