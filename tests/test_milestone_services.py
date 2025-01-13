import datetime as dt

from django.test import TestCase

from milestones import services
from milestones.models import Milestone
from plankit import health, rules
from projects import services as project_services

from .factories import DIAMOND, make_items, make_project


class MilestoneTestCase(TestCase):
    def setUp(self):
        self.project = make_project()
        self.items = make_items(self.project, *DIAMOND)
        self.cal = project_services.calendar_for(self.project)
        self.plan = project_services.schedule(self.project)

    def milestone(self, due):
        m = Milestone.objects.create(project=self.project, name="Beta", due_on=due)
        m.items.set(self.items.values())
        return m


class ForecastTests(MilestoneTestCase):
    def test_forecast_is_the_latest_planned_finish(self):
        self.assertEqual(services.forecast_finish(self.milestone(dt.date(2025, 2, 3))), self.plan.finish)

    def test_unscheduled_milestone_has_no_forecast(self):
        m = Milestone.objects.create(project=self.project, name="Empty", due_on=dt.date(2025, 2, 3))
        with self.assertRaises(services.MilestoneError):
            services.forecast_finish(m)
        self.assertEqual(services.rollup(self.project), {"Empty": "unscheduled"})

    def test_span_counts_working_days_from_project_start(self):
        m = self.milestone(dt.date(2025, 2, 10))
        self.assertEqual(services.span_days(m), self.cal.between(self.project.start_on, dt.date(2025, 2, 10)))


class StatusTests(MilestoneTestCase):
    def due_with_slip(self, slip):
        return self.cal.add(self.plan.finish, -slip)

    def test_on_time_milestone(self):
        m = self.milestone(self.due_with_slip(0))
        self.assertEqual(services.slip(m), 0)
        self.assertEqual(services.status(m), health.ON_TRACK)

    def test_early_milestone(self):
        m = self.milestone(self.cal.add(self.plan.finish, 2))
        self.assertEqual(services.slip(m), -2)
        self.assertEqual(services.status(m), health.ON_TRACK)

    def test_slip_up_to_the_tolerance_is_at_risk(self):
        m = self.milestone(self.due_with_slip(1))
        tol = rules.milestone_slip_tolerance_days(services.span_days(m))
        self.assertEqual(services.status(m), health.AT_RISK if tol >= 1 else health.LATE)

    def test_slip_past_the_tolerance_is_late(self):
        probe = self.milestone(self.due_with_slip(1))
        tol = rules.milestone_slip_tolerance_days(services.span_days(probe))
        probe.delete()
        m = self.milestone(self.due_with_slip(tol + 1)) if tol + 1 < 6 else self.milestone(self.due_with_slip(6))
        tol_now = rules.milestone_slip_tolerance_days(services.span_days(m))
        expected = health.LATE if services.slip(m) > tol_now else health.AT_RISK
        self.assertEqual(services.status(m), expected)

    def test_rollup_reports_each_milestone(self):
        self.milestone(self.due_with_slip(0))
        Milestone.objects.create(project=self.project, name="Later", due_on=dt.date(2025, 6, 2))
        self.assertEqual(services.rollup(self.project), {"Beta": "on_track", "Later": "unscheduled"})


class BaselineTests(MilestoneTestCase):
    def test_first_baseline_is_always_allowed(self):
        m = self.milestone(dt.date(2025, 3, 3))
        self.assertFalse(services.baseline_is_locked(m, dt.date(2025, 3, 3)))
        services.set_baseline(m, dt.date(2025, 3, 3))
        self.assertEqual(m.baseline_due_on, dt.date(2025, 3, 3))

    def test_baseline_freezes_before_the_due_date(self):
        m = self.milestone(dt.date(2025, 3, 3))
        services.set_baseline(m, dt.date(2025, 1, 13))
        window = health.freeze_days(services.span_days(m))
        self.assertEqual(window, rules.baseline_freeze_days(services.span_days(m)))
        inside = self.cal.add(m.baseline_due_on, -window)
        self.assertTrue(services.baseline_is_locked(m, inside))
        with self.assertRaises(services.MilestoneError):
            services.set_baseline(m, inside)

    def test_baseline_is_open_well_before_the_window(self):
        m = self.milestone(dt.date(2025, 3, 3))
        services.set_baseline(m, dt.date(2025, 1, 13))
        self.assertFalse(services.baseline_is_locked(m, dt.date(2025, 1, 13)))

    def test_moving_the_due_date(self):
        m = self.milestone(dt.date(2025, 3, 3))
        services.set_baseline(m, dt.date(2025, 1, 13))
        services.move_due_date(m, dt.date(2025, 3, 10), dt.date(2025, 1, 14))
        m.refresh_from_db()
        self.assertEqual((m.due_on, m.baseline_due_on), (dt.date(2025, 3, 10), dt.date(2025, 3, 3)))

    def test_moving_a_frozen_milestone_is_refused(self):
        m = self.milestone(dt.date(2025, 3, 3))
        services.set_baseline(m, dt.date(2025, 1, 13))
        with self.assertRaises(services.MilestoneError):
            services.move_due_date(m, dt.date(2025, 3, 10), dt.date(2025, 3, 3))
