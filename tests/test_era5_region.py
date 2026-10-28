"""Check sample weighting and reject an unexpected grid mapping."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from ind320 import era5_region
class RegionalWeatherChecks(unittest.TestCase):
    def test_grid_sharing_preserves_all_sample_weights(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'data/regions').mkdir(parents=True)
            # Unequal occupation catches the error of averaging grid cells equally.
            points = pd.DataFrame({'region': 'NO3', 'region_type': 'electricity',
                                   'point_id': range(1000),
                                   'latitude': np.r_[np.full(900, 63.01), np.full(100, 64.01)],
                                   'longitude': 10.01})
            points.to_csv(root / 'data/regions/sampled_locations.csv', index=False)
            def response(url, timeout):
                latitude = 63.0 if 'latitude=63.01' in url else 64.0
                value = 1.0 if latitude == 63 else 11.0
                payload = {'latitude': latitude, 'longitude': 10.0,
                           'hourly_units': {'temperature_2m': '°C', 'precipitation': 'mm'},
                           'hourly': {'time': pd.date_range('2024-01-01', periods=24, freq='h').strftime('%Y-%m-%dT%H:%M').tolist(),
                                      'temperature_2m': [value] * 24, 'precipitation': [value] * 24}}
                return io.BytesIO(json.dumps(payload).encode())
            with patch.object(era5_region, 'ROOT', root), patch.object(era5_region, 'urlopen', side_effect=response) as fetch, patch.object(era5_region.time, 'sleep'):
                result = era5_region.regional_weather('NO3', '2024-01-01', '2024-01-01', cache_dir=root / 'cache')
                self.assertTrue(np.allclose(result.temperature_2m, 2.0))
                self.assertTrue(result.sample_count.eq(1000).all())
                self.assertEqual(fetch.call_count, 2)
                # A repeat uses saved responses and makes no further requests.
                era5_region.regional_weather('NO3', '2024-01-01', '2024-01-01', cache_dir=root / 'cache')
                self.assertEqual(fetch.call_count, 2)


if __name__ == '__main__':
    unittest.main()
