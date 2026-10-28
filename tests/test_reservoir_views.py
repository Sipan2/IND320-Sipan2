"""Regression checks for the shared measurement and area-comparison page."""
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class ReservoirViewsChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.observations = pd.read_csv(ROOT / 'data/reservoirs/nve_snapshot.csv', parse_dates=['date'])
        cls.metadata = pd.read_json(ROOT / 'data/regions/nve_area_catalogue.json')

    def page(self):
        return AppTest.from_file(str(ROOT / 'pages/2_Plots.py'), default_timeout=60).run()

    def test_text_measurement_keeps_area_comparison_visible(self):
        with patch('ind320.data_utils.load_data', return_value=self.observations), patch('ind320.reservoir_views.load_areas', return_value=self.metadata):
            app = self.page()
            app.selectbox[1].set_value('area_type').run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.get('vega_lite_chart')), 1)

    def test_area_families_and_interval_update_both_views(self):
        with patch('ind320.data_utils.load_data', return_value=self.observations), patch('ind320.reservoir_views.load_areas', return_value=self.metadata):
            app = self.page()
            for family in ['VASS', 'NO', 'EL']:
                app.radio[0].set_value(family).run()
                self.assertFalse(app.exception)
                self.assertEqual(len(app.get('vega_lite_chart')), 1)
            months = self.observations.date.dt.strftime('%Y-%m').sort_values().unique().tolist()
            app.select_slider[0].set_value((months[-12], months[-1])).run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.get('vega_lite_chart')), 1)


if __name__ == '__main__':
    unittest.main()
