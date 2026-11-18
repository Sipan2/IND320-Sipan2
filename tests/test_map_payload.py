"""Ensure the faster map preserves every boundary coordinate."""
import base64
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from ind320.map_component import boundary_payload

ROOT = Path(__file__).resolve().parents[1]


class MapPayloadChecks(unittest.TestCase):
    def test_both_boundary_families_are_lossless(self):
        for name in ('electricity', 'assignment_precipitation'):
            with self.subTest(name=name):
                path = ROOT / 'data/regions' / (name + '.geojson')
                payload = boundary_payload(str(path), path.stat().st_mtime_ns)
                restored = json.loads(gzip.decompress(base64.b64decode(payload['gzip'])))
                self.assertEqual(restored, json.loads(path.read_text()))
                self.assertLess(len(payload['gzip']), path.stat().st_size)

    def test_changed_file_invalidates_the_payload(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'areas.json'
            path.write_text('{"features": []}')
            first = boundary_payload(str(path), 1)
            path.write_text('{"features": [], "updated": true}')
            second = boundary_payload(str(path), 2)
            self.assertNotEqual(first['id'], second['id'])
            restored = json.loads(gzip.decompress(base64.b64decode(second['gzip'])))
            self.assertTrue(restored['updated'])
