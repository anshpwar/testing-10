import datetime as dt
import unittest

from plankit import estimates, health, rules
from plankit.workcal import WorkCalendar

DUE = dt.date(2025, 3, 3)  # a Monday


class EstimateTests(unittest.TestCase):
    def test_three_point(self):
        self.assertEqual(estimates.three_point(2, 4, 8), 4)
        self.assertEqual(estimates.three_point(3, 4, 8), 5)
        self.assertEqual(estimates.three_point(1, 1, 1), 1)

    def test_three_point_validates_order(self):
        for args in ((0, 1, 2), (3, 2, 4), (1, 5, 4)):
            with self.assertRaises(ValueError):
                estimates.three_point(*args)

    def test_padded_range_uses_the_confidence_rule(self):
        low, high = estimates.padded_range([3, 5, 2, 10])
        gap = 100 - rules.estimate_confidence_pct(4)
        self.assertEqual(low, 20)
        self.assertEqual(high, 20 + -(-20 * gap // 100))

    def test_confidence_never_exceeds_one_hundred(self):
        for n in (1, 5, 6, 30, 100):
            self.assertLessEqual(estimates.confidence_pct(n), 100)

    def test_split_estimate(self):
        self.assertEqual(estimates.split_estimate(10, 3), [4, 3, 3])
        self.assertEqual(estimates.split_estimate(2, 4), [1, 1, 0, 0])
        with self.assertRaises(ValueError):
            estimates.split_estimate(5, 0)


class SlipTests(unittest.TestCase):
    def setUp(self):
        self.cal = WorkCalendar()

    def test_early_or_on_time_is_on_track(self):
        self.assertEqual(health.slip_status(self.cal, DUE, DUE, 40), health.ON_TRACK)
        self.assertEqual(health.slip_status(self.cal, DUE, self.cal.add(DUE, -2), 40), health.ON_TRACK)

    def test_slip_within_tolerance_is_at_risk(self):
        tol = health.slip_tolerance(40)
        self.assertEqual(tol, rules.milestone_slip_tolerance_days(40))
        forecast = self.cal.add(DUE, tol)
        self.assertEqual(health.slip_days(self.cal, DUE, forecast), tol)
        self.assertEqual(health.slip_status(self.cal, DUE, forecast, 40), health.AT_RISK if tol else health.ON_TRACK)

    def test_slip_beyond_tolerance_is_late(self):
        tol = health.slip_tolerance(40)
        forecast = self.cal.add(DUE, tol + 1)
        self.assertEqual(health.slip_status(self.cal, DUE, forecast, 40), health.LATE)

    def test_negative_slip_when_early(self):
        self.assertEqual(health.slip_days(self.cal, DUE, self.cal.add(DUE, -3)), -3)


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.cal = WorkCalendar()

    def test_frozen_inside_the_window(self):
        window = health.freeze_days(40)
        self.assertEqual(window, rules.baseline_freeze_days(40))
        self.assertTrue(health.baseline_locked(self.cal, self.cal.add(DUE, -window), DUE, 40))

    def test_open_before_the_window(self):
        window = health.freeze_days(40)
        self.assertFalse(health.baseline_locked(self.cal, self.cal.add(DUE, -(window + 1)), DUE, 40))

    def test_frozen_after_the_due_date(self):
        self.assertTrue(health.baseline_locked(self.cal, self.cal.add(DUE, 3), DUE, 40))
