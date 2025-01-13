import datetime as dt
import unittest

from plankit import cadence, capacity, rules
from plankit.workcal import WorkCalendar

MONDAY = dt.date(2025, 1, 13)
ONE_DAY = dt.timedelta(days=1)


class SprintTests(unittest.TestCase):
    def test_length_comes_from_the_rule(self):
        self.assertEqual(cadence.sprint_length(6), rules.sprint_length_days(6))

    def test_windows_hold_exactly_one_sprint_of_working_days(self):
        cal = WorkCalendar(holidays=[dt.date(2025, 1, 20)])
        windows = cadence.sprint_windows(MONDAY, cal, 6, 3)
        length = cadence.sprint_length(6)
        for first, last in windows:
            self.assertEqual(cal.between(first, last + ONE_DAY), length)

    def test_windows_are_back_to_back(self):
        cal = WorkCalendar()
        windows = cadence.sprint_windows(MONDAY, cal, 6, 4)
        self.assertEqual(windows[0][0], MONDAY)
        for (_, last), (nxt_first, _) in zip(windows, windows[1:]):
            self.assertEqual(nxt_first, cal.next_workday(last + ONE_DAY))

    def test_start_on_weekend_rolls_forward(self):
        windows = cadence.sprint_windows(dt.date(2025, 1, 18), WorkCalendar(), 6, 1)
        self.assertEqual(windows[0][0], dt.date(2025, 1, 20))

    def test_sprint_index(self):
        windows = cadence.sprint_windows(MONDAY, WorkCalendar(), 6, 3)
        self.assertEqual(cadence.sprint_index(windows, windows[1][0]), 1)
        self.assertEqual(cadence.sprint_index(windows, windows[2][1]), 2)
        self.assertIsNone(cadence.sprint_index(windows, dt.date(2024, 12, 31)))

    def test_standup_load(self):
        self.assertEqual(cadence.standup_minutes_per_sprint(6), rules.standup_minutes(6) * rules.sprint_length_days(6))
        self.assertEqual(cadence.meeting_share_pct(6, 600), rules.standup_minutes(6) * 100 // 600)


class CapacityTests(unittest.TestCase):
    def test_person_days_after_cover(self):
        cal = WorkCalendar()
        gross = 10 * 5
        cover = rules.holiday_cover_pct(5)
        self.assertEqual(capacity.person_days(cal, MONDAY, dt.date(2025, 1, 27), 5), gross - -(-gross * cover // 100))

    def test_person_days_ignore_weekends_and_holidays(self):
        cal = WorkCalendar(holidays=[dt.date(2025, 1, 15)])
        days = capacity.person_days(cal, MONDAY, dt.date(2025, 1, 20), 1)
        self.assertLessEqual(days, 4)
        self.assertGreaterEqual(days, 4 - -(-4 * rules.holiday_cover_pct(1) // 100))

    def test_wip(self):
        limit = rules.wip_limit(6)
        self.assertEqual(capacity.wip_limit(6), limit)
        self.assertEqual(capacity.wip_available(6, 0), limit)
        self.assertEqual(capacity.wip_available(6, limit), 0)
        self.assertEqual(capacity.wip_available(6, limit + 3), 0)

    def test_assignment_room(self):
        cap = rules.max_assignments_per_person(2)
        self.assertEqual(capacity.assignment_cap(2), cap)
        self.assertEqual(capacity.assignment_room(2, 1), cap - 1)
        self.assertEqual(capacity.assignment_room(2, cap), 0)

    def test_utilisation(self):
        self.assertEqual(capacity.utilisation_pct(8, 10), 80)
        self.assertEqual(capacity.utilisation_pct(0, 0), 0)
        self.assertEqual(capacity.utilisation_pct(3, 0), 999)
