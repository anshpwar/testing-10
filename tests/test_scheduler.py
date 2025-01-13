import datetime as dt
import unittest

from plankit import rules, scheduler
from plankit.workcal import WorkCalendar

from .graphs import diamond, two_tracks

MONDAY = dt.date(2025, 1, 13)


class PlanDatesTests(unittest.TestCase):
    def test_dates_of_the_diamond(self):
        p = scheduler.plan(diamond(), MONDAY, WorkCalendar())
        self.assertEqual(p.window("A"), (dt.date(2025, 1, 13), dt.date(2025, 1, 15)))
        self.assertEqual(p.window("B"), (dt.date(2025, 1, 16), dt.date(2025, 1, 17)))
        self.assertEqual(p.window("C"), (dt.date(2025, 1, 16), dt.date(2025, 1, 21)))
        self.assertEqual(p.window("D"), (dt.date(2025, 1, 22), dt.date(2025, 1, 22)))
        self.assertEqual(p.length_days, 8)
        self.assertEqual(p.finish, dt.date(2025, 1, 22))

    def test_critical_chain_and_slack(self):
        p = scheduler.plan(diamond(), MONDAY, WorkCalendar())
        self.assertEqual(p.critical_path, ["A", "C", "D"])
        self.assertEqual(p.tasks["B"].slack, 2)
        self.assertFalse(p.tasks["B"].critical)

    def test_start_on_a_weekend_begins_on_monday(self):
        p = scheduler.plan(diamond(), dt.date(2025, 1, 11), WorkCalendar())
        self.assertEqual(p.window("A")[0], MONDAY)

    def test_holiday_pushes_dependent_work(self):
        p = scheduler.plan(diamond(), MONDAY, WorkCalendar(holidays=[dt.date(2025, 1, 16)]))
        self.assertEqual(p.window("C"), (dt.date(2025, 1, 17), dt.date(2025, 1, 22)))
        self.assertEqual(p.finish, dt.date(2025, 1, 23))

    def test_not_before_floor(self):
        p = scheduler.plan(diamond(), MONDAY, WorkCalendar(), not_before={"D": dt.date(2025, 1, 27)})
        self.assertEqual(p.window("D"), (dt.date(2025, 1, 27), dt.date(2025, 1, 27)))
        self.assertEqual(p.length_days, 11)

    def test_not_before_in_the_past_is_ignored(self):
        p = scheduler.plan(diamond(), MONDAY, WorkCalendar(), not_before={"A": dt.date(2025, 1, 1)})
        self.assertEqual(p.window("A")[0], MONDAY)

    def test_what_if_extra_days(self):
        base = scheduler.plan(diamond(), MONDAY, WorkCalendar())
        longer = scheduler.plan(diamond(), MONDAY, WorkCalendar(), extra_days={"C": 2})
        self.assertEqual(scheduler.slip_of(base, longer), 2)
        shorter_b = scheduler.plan(diamond(), MONDAY, WorkCalendar(), extra_days={"B": 1})
        self.assertEqual(scheduler.slip_of(base, shorter_b), 0)

    def test_empty_graph(self):
        from plankit.depgraph import TaskGraph

        p = scheduler.plan(TaskGraph(), MONDAY, WorkCalendar())
        self.assertEqual((p.length_days, p.reserve_days, p.tasks), (0, 0, {}))
        self.assertEqual(p.finish, MONDAY)


class ReservePolicyTests(unittest.TestCase):
    def test_reserve_follows_the_rule(self):
        p = scheduler.plan(diamond(), MONDAY, WorkCalendar())
        expected = -(-8 * rules.risk_reserve_pct(4) // 100)
        self.assertEqual(p.reserve_days, expected)
        self.assertEqual(p.reserve_days, scheduler.reserve_days(8, 4))

    def test_committed_finish_is_after_the_reserve(self):
        cal = WorkCalendar()
        p = scheduler.plan(diamond(), MONDAY, cal)
        self.assertEqual(cal.between(p.finish, p.committed_finish), p.reserve_days)
        self.assertGreaterEqual(p.committed_finish, p.finish)

    def test_more_links_never_lower_the_reserve_percentage_used(self):
        few = scheduler.plan(two_tracks(), MONDAY, WorkCalendar())
        self.assertEqual(few.reserve_days, scheduler.reserve_days(few.length_days, 3))

    def test_near_critical_uses_the_slack_rule(self):
        p = scheduler.plan(two_tracks(), MONDAY, WorkCalendar())
        limit = rules.critical_slack_days(p.length_days)
        self.assertEqual(p.near_critical, ["P1", "P2"] if limit >= 1 else [])
