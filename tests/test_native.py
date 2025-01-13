import ctypes
import datetime as dt
import pathlib
import re
import unittest

from plankit import native

HEADERS = pathlib.Path(__file__).resolve().parent.parent / "c" / "include"
MONDAY = dt.date(2025, 1, 13)


def header_constants():
    out = {}
    for path in HEADERS.glob("*.h"):
        for m in re.finditer(r"#define (PK_\w+) \(?(-?\d+)\)?\s*(?:/\*.*)?$", path.read_text(), re.M):
            out[m.group(1)] = int(m.group(2))
    return out


class LayoutTests(unittest.TestCase):
    def test_calendar_layout_matches_library(self):
        self.assertEqual(ctypes.sizeof(native.PkCalendar), native.calendar_sizeof())

    def test_depset_layout_matches_library(self):
        self.assertEqual(ctypes.sizeof(native.PkDepset), native.depset_sizeof())

    def test_known_sizes(self):
        self.assertEqual(native.calendar_sizeof(), 264)
        self.assertEqual(native.depset_sizeof(), 24)

    def test_status_codes_mirror_headers(self):
        consts = header_constants()
        self.assertEqual(consts["PK_ERR_ARG"], native.ERR_ARG)
        self.assertEqual(consts["PK_ERR_RANGE"], native.ERR_RANGE)
        self.assertEqual(consts["PK_ERR_FULL"], native.ERR_FULL)
        self.assertEqual(consts["PK_ERR_CYCLE"], native.ERR_CYCLE)
        self.assertEqual(consts["PK_ERR_NOWORK"], native.ERR_NOWORK)

    def test_capacities_mirror_headers(self):
        consts = header_constants()
        self.assertEqual(consts["PK_MAX_HOLIDAYS"], native.MAX_HOLIDAYS)
        self.assertEqual(consts["PK_MAX_TASKS"], native.MAX_TASKS)
        self.assertEqual(consts["PK_DAY_MAX"], native.DAY_MAX)

    def test_weekday_numbers_mirror_headers(self):
        consts = header_constants()
        for i, name in enumerate(["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]):
            self.assertEqual(consts[f"PK_{name}"], i)
        self.assertEqual(native.SUN, 6)


class DayNumberTests(unittest.TestCase):
    def test_epoch_and_known_day(self):
        self.assertEqual(native.to_day(dt.date(1970, 1, 1)), 0)
        self.assertEqual(native.to_day(MONDAY), 20101)

    def test_round_trip(self):
        for date in (dt.date(2000, 2, 29), MONDAY, dt.date(2031, 12, 31)):
            self.assertEqual(native.from_day(native.to_day(date)), date)

    def test_weekday(self):
        self.assertEqual(native.weekday(MONDAY), native.MON)
        self.assertEqual(native.weekday(dt.date(1970, 1, 1)), native.THU)
        self.assertEqual(native.weekday(dt.date(2025, 1, 19)), native.SUN)

    def test_dates_before_the_epoch_are_rejected(self):
        with self.assertRaises(native.NativeError) as ctx:
            native.weekday(dt.date(1969, 12, 31))
        self.assertEqual(ctx.exception.code, native.ERR_RANGE)


class CalendarTests(unittest.TestCase):
    def test_default_week(self):
        cal = native.make_calendar()
        self.assertTrue(native.is_workday(cal, MONDAY))
        self.assertTrue(native.is_workday(cal, dt.date(2025, 1, 17)))
        self.assertFalse(native.is_workday(cal, dt.date(2025, 1, 18)))

    def test_holidays_are_not_working_days(self):
        cal = native.make_calendar(holidays=[dt.date(2025, 1, 15)])
        self.assertFalse(native.is_workday(cal, dt.date(2025, 1, 15)))
        self.assertEqual(native.add_workdays(cal, MONDAY, 2), dt.date(2025, 1, 16))

    def test_holiday_list_is_sorted_and_unique(self):
        cal = native.make_calendar(holidays=[dt.date(2025, 2, 3), dt.date(2025, 1, 15), dt.date(2025, 2, 3)])
        self.assertEqual(cal.holiday_count, 2)
        self.assertEqual(list(cal.holidays)[:2], sorted(list(cal.holidays)[:2]))

    def test_too_many_holidays(self):
        days = [MONDAY + dt.timedelta(days=i) for i in range(native.MAX_HOLIDAYS + 1)]
        with self.assertRaises(native.NativeError) as ctx:
            native.make_calendar(holidays=days)
        self.assertEqual(ctx.exception.code, native.ERR_FULL)

    def test_empty_workweek_is_rejected(self):
        with self.assertRaises(native.NativeError) as ctx:
            native.make_calendar(0)
        self.assertEqual(ctx.exception.code, native.ERR_ARG)

    def test_arithmetic(self):
        cal = native.make_calendar()
        self.assertEqual(native.add_workdays(cal, MONDAY, 5), dt.date(2025, 1, 20))
        self.assertEqual(native.add_workdays(cal, dt.date(2025, 1, 18), 0), dt.date(2025, 1, 20))
        self.assertEqual(native.add_workdays(cal, dt.date(2025, 1, 20), -1), dt.date(2025, 1, 17))
        self.assertEqual(native.workdays_between(cal, MONDAY, dt.date(2025, 1, 20)), 5)
        self.assertEqual(native.workdays_between(cal, dt.date(2025, 1, 20), MONDAY), -5)
        self.assertEqual(native.finish_day(cal, MONDAY, 6), dt.date(2025, 1, 20))
        self.assertEqual(native.next_workday(cal, dt.date(2025, 1, 19)), MONDAY + dt.timedelta(days=7))

    def test_finish_day_needs_a_positive_duration(self):
        with self.assertRaises(native.NativeError):
            native.finish_day(native.make_calendar(), MONDAY, 0)


class DependencySetTests(unittest.TestCase):
    def test_closure_of_a_chain(self):
        closed = native.closure(4, [(3, 2), (2, 1), (1, 0)])
        self.assertEqual(closed, [[], [0], [0, 1], [0, 1, 2]])

    def test_closure_of_a_diamond(self):
        closed = native.closure(4, [(1, 0), (2, 0), (3, 1), (3, 2)])
        self.assertEqual(closed[3], [0, 1, 2])
        self.assertEqual(closed[1], [0])

    def test_cycle_is_reported(self):
        with self.assertRaises(native.NativeError) as ctx:
            native.closure(3, [(0, 1), (1, 2), (2, 0)])
        self.assertEqual(ctx.exception.code, native.ERR_CYCLE)

    def test_sets_beyond_the_first_word(self):
        closed = native.closure(100, [(99, 70), (70, 3)])
        self.assertEqual(closed[99], [3, 70])

    def test_edge_out_of_range(self):
        with self.assertRaises(native.NativeError) as ctx:
            native.closure(3, [(0, 7)])
        self.assertEqual(ctx.exception.code, native.ERR_RANGE)

    def test_count(self):
        sets = native.make_depsets(5, [(4, 0), (4, 2), (4, 3)])
        self.assertEqual(native.dep_count(sets[4]), 3)
        self.assertEqual(native.dep_count(sets[0]), 0)
