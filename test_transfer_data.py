"""Small checks for gaps, compressed values and energy conversion."""
import unittest
from transfer_data import parse_flow


def response(curve, points):
    return f"""<root><TimeSeries><out_Domain.mRID>NO</out_Domain.mRID>
    <in_Domain.mRID>DK</in_Domain.mRID><quantity_Measure_Unit.name>MAW</quantity_Measure_Unit.name>
    <curveType>{curve}</curveType><Period><timeInterval><start>2025-01-01T00:00Z</start>
    <end>2025-01-01T01:00Z</end></timeInterval><resolution>PT15M</resolution>
    {''.join(f'<Point><position>{p}</position><quantity>{q}</quantity></Point>' for p,q in points)}
    </Period></TimeSeries></root>"""


class FlowTests(unittest.TestCase):
    def test_compressed_blocks(self):
        rows = parse_flow(response('A03', [(1, 100), (3, 200)]), 'NO', 'DK')
        self.assertEqual([r['power_mw'] for r in rows], [100, 100, 200, 200])
        self.assertEqual(sum(r['energy_mwh'] for r in rows), 150)

    def test_missing_a01_is_not_zero_or_forward_filled(self):
        rows = parse_flow(response('A01', [(1, 100), (3, 200)]), 'NO', 'DK')
        self.assertEqual(len(rows), 2)
        self.assertEqual(sum(r['energy_mwh'] for r in rows), 75)

    def test_wrong_direction_rejected(self):
        with self.assertRaises(ValueError):
            parse_flow(response('A03', [(1, 0)]), 'DK', 'NO')

    def test_duplicate_position_rejected(self):
        with self.assertRaises(ValueError):
            parse_flow(response('A03', [(1, 100), (1, 200)]), 'NO', 'DK')


if __name__ == '__main__':
    unittest.main()
