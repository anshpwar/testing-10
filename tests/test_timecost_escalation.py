import datetime as dt
import unittest

from plankit import escalation, rules, timecost
from plankit.workcal import WorkCalendar

MONDAY = dt.date(2025, 3, 3)


class DailyLimitTests(unittest.TestCase):
    def test_limit_is_the_rule_in_minutes(self):
        for level in (1, 2, 3, 4):
            self.assertEqual(timecost.daily_limit_minutes(level), rules.max_daily_hours(level) * 60)

    def test_room_boundary(self):
        limit = timecost.daily_limit_minutes(2)
        self.assertTrue(timecost.day_has_room(2, limit - 60, 60))
        self.assertFalse(timecost.day_has_room(2, limit - 60, 61))
        self.assertFalse(timecost.day_has_room(2, limit, 1))


class LockTests(unittest.TestCase):
    def setUp(self):
        self.cal = WorkCalendar()

    def test_entry_is_open_up_to_the_window(self):
        window = timecost.lock_window_days(8)
        self.assertEqual(window, rules.timesheet_lock_days(8))
        self.assertFalse(timecost.is_locked(self.cal, MONDAY, self.cal.add(MONDAY, window), 8))

    def test_entry_locks_one_day_later(self):
        window = timecost.lock_window_days(8)
        self.assertTrue(timecost.is_locked(self.cal, MONDAY, self.cal.add(MONDAY, window + 1), 8))

    def test_weekends_do_not_age_an_entry(self):
        friday = dt.date(2025, 3, 7)
        self.assertEqual(self.cal.between(friday, dt.date(2025, 3, 10)), 1)
        self.assertEqual(timecost.is_locked(self.cal, friday, dt.date(2025, 3, 10), 8), timecost.lock_window_days(8) < 1)


class CostTests(unittest.TestCase):
    RATE = 6000  # cents per hour

    def test_regular_week_has_no_premium(self):
        self.assertEqual(timecost.weekly_cost_cents(40 * 60, self.RATE), 40 * self.RATE)
        self.assertEqual(timecost.weekly_cost_cents(10 * 60, self.RATE), 10 * self.RATE)
        self.assertEqual(timecost.weekly_cost_cents(0, self.RATE), 0)

    def test_overtime_uses_the_multiplier_for_the_whole_week(self):
        minutes = 45 * 60
        pct = rules.overtime_multiplier_pct(45)
        self.assertEqual(timecost.overtime_multiplier_pct(minutes), pct)
        expected = 40 * self.RATE + 5 * self.RATE * pct // 100
        self.assertEqual(timecost.weekly_cost_cents(minutes, self.RATE), expected)

    def test_partial_hour_is_not_lost(self):
        minutes = 40 * 60 + 30
        pct = rules.overtime_multiplier_pct(minutes // 60)
        self.assertEqual(timecost.weekly_cost_cents(minutes, self.RATE), 40 * self.RATE + 30 * self.RATE * pct // 6000)


class EscalationTests(unittest.TestCase):
    def setUp(self):
        self.cal = WorkCalendar()

    def test_due_exactly_after_the_priority_period(self):
        for priority in (1, 2, 3, 4):
            after = escalation.escalation_after(priority)
            self.assertEqual(after, rules.escalation_after_days(priority))
            self.assertTrue(escalation.is_due(self.cal, MONDAY, self.cal.add(MONDAY, after), priority))

    def test_not_due_a_day_early(self):
        priority = 4
        after = escalation.escalation_after(priority)
        if after:
            self.assertFalse(escalation.is_due(self.cal, MONDAY, self.cal.add(MONDAY, after - 1), priority))

    def test_due_date_matches_is_due(self):
        for priority in (1, 3):
            day = escalation.due_date(self.cal, MONDAY, priority)
            self.assertTrue(escalation.is_due(self.cal, MONDAY, day, priority))

    def test_overdue_by(self):
        priority = 2
        after = escalation.escalation_after(priority)
        today = self.cal.add(MONDAY, after + 2)
        self.assertEqual(escalation.overdue_by(self.cal, MONDAY, today, priority), 2)
        self.assertEqual(escalation.overdue_by(self.cal, MONDAY, MONDAY, priority), 0)
