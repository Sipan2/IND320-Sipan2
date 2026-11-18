"""Guard training-window and recursive-forecast behaviour from Part 4."""
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest
from ind320.forecast import forecast_filling

ROOT = Path(__file__).resolve().parents[1]

class ForecastChecks(unittest.TestCase):
    def setUp(self):
        self.data = pd.read_parquet(ROOT / 'data/reservoirs/nve_snapshot.parquet')
        self.y = self.data.query("area_type == 'EL' and area_number == 3").set_index('date').filling_ratio.sort_index()

    def test_default_page_uses_104_observations(self):
        with patch('ind320.data_utils.load_data', return_value=self.data):
            app = AppTest.from_file(str(ROOT / 'pages/7_Forecast.py')).run()
            self.assertFalse(app.exception)
            self.assertTrue(any('Training observations: 104 weeks' in c.value for c in app.caption))
            self.assertFalse(app.warning)
            app.select_slider[0].set_value(('2024-01', '2024-12')).run()
            self.assertFalse(app.exception)
            self.assertTrue(any('only 52 weekly observations' in w.value for w in app.warning))

    def test_recursive_dates_and_external_variables(self):
        y = self.y.tail(104)
        x = pd.DataFrame({'temperature': np.sin(np.arange(len(y))/8)}, index=y.index)
        for inputs in [None, x]:
            prediction = forecast_filling(y, history=104, horizon=12, inputs=inputs)
            self.assertEqual(len(prediction), 12)
            self.assertEqual(prediction.index[0], y.index[-1] + pd.Timedelta(weeks=1))
            self.assertTrue(np.isfinite(prediction).all())
            self.assertTrue(prediction.between(0, 1).all())

    def test_missing_and_irregular_observations_are_rejected(self):
        y = self.y.tail(104)
        with self.assertRaises(ValueError):
            forecast_filling(y.drop(y.index[20]))
        with self.assertRaises(ValueError):
            forecast_filling(y.mask(y.index == y.index[20]))

if __name__ == '__main__':
    unittest.main()
