import unittest

from plankit import calc


class CalcTests(unittest.TestCase):
    def test_combined_charge(self):
        self.assertEqual(calc.combined_charge(0), 14)
        self.assertEqual(calc.combined_charge(1), 14)
        self.assertEqual(calc.combined_charge(3), 14)
        self.assertEqual(calc.combined_charge(4), 24)
