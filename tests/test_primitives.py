"""Unit tests for the primitive factory."""

import unittest
from acrilib.primitives import factory


class TestPrimitives(unittest.TestCase):
    """Test suite for the geometry primitive factory."""

    def test_create_line(self):
        """Tests the creation of line geometry data."""
        plane_context = {'origin': [0,0,0], 'u_axis': [1,0,0], 'v_axis': [0,1,0]}
        data = factory.create_line(1, 2, 3, 4, **plane_context)
        self.assertIn('points', data)
        self.assertIn('cells', data)
        self.assertIn('type', data)
        self.assertEqual(data['type'], 'lines')
        self.assertEqual(len(data['points']), 2)
        self.assertListEqual(data['points'][0], [1, 2, 0])
        self.assertListEqual(data['points'][1], [3, 4, 0])
        self.assertListEqual(data['cells'], [[0, 1]])


if __name__ == '__main__':
    unittest.main()