import datetime as dt
import unittest

from plankit.workcal import WorkCalendar

MONDAY = dt.date(2025, 1, 13)


class WorkCalendarTests(unittest.TestCase):
    def test_default_week_is_monday_to_friday(self):
        cal = WorkCalendar()
        self.assertEqual(cal.working_weekdays(), [0, 1, 2, 3, 4])
        self.assertTrue(cal.is_workday(MONDAY))
        self.assertFalse(cal.is_workday(dt.date(2025, 1, 12)))

    def test_from_weekdays(self):
        cal = WorkCalendar.from_weekdays([0, 2, 4])
        self.assertEqual(cal.working_weekdays(), [0, 2, 4])
        self.assertEqual(cal.add(MONDAY, 1), dt.date(2025, 1, 15))
        self.assertEqual(cal.add(MONDAY, 3), dt.date(2025, 1, 20))

    def test_holidays_are_deduplicated_and_sorted(self):
        cal = WorkCalendar(holidays=[dt.date(2025, 2, 3), dt.date(2025, 1, 20), dt.date(2025, 2, 3)])
        self.assertEqual(cal.holidays, (dt.date(2025, 1, 20), dt.date(2025, 2, 3)))

    def test_holiday_moves_the_next_workday(self):
        cal = WorkCalendar(holidays=[MONDAY])
        self.assertEqual(cal.next_workday(MONDAY), dt.date(2025, 1, 14))

    def test_span_of_a_task(self):
        cal = WorkCalendar()
        self.assertEqual(cal.span(MONDAY, 1), (MONDAY, MONDAY))
        self.assertEqual(cal.span(MONDAY, 6), (MONDAY, dt.date(2025, 1, 20)))
        self.assertEqual(cal.span(dt.date(2025, 1, 18), 2), (dt.date(2025, 1, 20), dt.date(2025, 1, 21)))

    def test_between_counts_a_half_open_interval(self):
        cal = WorkCalendar()
        self.assertEqual(cal.between(MONDAY, dt.date(2025, 1, 17)), 4)
        self.assertEqual(cal.between(MONDAY, dt.date(2025, 1, 18)), 5)
        self.assertEqual(cal.between(dt.date(2025, 1, 17), MONDAY), -4)

    def test_working_dates(self):
        cal = WorkCalendar(holidays=[dt.date(2025, 1, 15)])
        got = cal.working_dates(MONDAY, dt.date(2025, 1, 20))
        self.assertEqual(got, [dt.date(2025, 1, 13), dt.date(2025, 1, 14), dt.date(2025, 1, 16), dt.date(2025, 1, 17)])

    def test_add_and_between_agree(self):
        cal = WorkCalendar(holidays=[dt.date(2025, 1, 22)])
        for n in range(0, 15):
            self.assertEqual(cal.between(MONDAY, cal.add(MONDAY, n)), n)

    def test_too_many_holidays(self):
        days = [MONDAY + dt.timedelta(days=i) for i in range(65)]
        with self.assertRaises(ValueError):
            WorkCalendar(holidays=days)
