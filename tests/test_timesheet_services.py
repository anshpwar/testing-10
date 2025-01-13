import datetime as dt

from django.test import TestCase

from plankit import rules
from projects import services as project_services
from timesheets import services
from timesheets.models import TimeEntry

from .factories import START, make_items, make_project


class LogTimeTests(TestCase):
    def setUp(self):
        self.project = make_project()
        self.item = make_items(self.project, {"T1": 5})["T1"]
        self.senior = self.project.members.get(seniority=3)
        self.junior = self.project.members.get(seniority=1)

    def test_log_and_total(self):
        services.log_time(self.junior, self.item, START, 120, START, note="design")
        services.log_time(self.junior, self.item, START, 60, START)
        self.assertEqual(services.minutes_on(self.junior, START), 180)
        self.assertEqual(services.item_minutes(self.item), 180)

    def test_rejects_non_positive_minutes(self):
        with self.assertRaises(services.TimesheetError):
            services.log_time(self.junior, self.item, START, 0, START)

    def test_rejects_weekends_future_dates_and_foreign_items(self):
        with self.assertRaises(services.TimesheetError):
            services.log_time(self.junior, self.item, dt.date(2025, 1, 18), 60, dt.date(2025, 1, 20))
        with self.assertRaises(services.TimesheetError):
            services.log_time(self.junior, self.item, dt.date(2025, 1, 14), 60, START)
        other = make_items(make_project("ORBIT"), {"X": 1})["X"]
        with self.assertRaises(services.TimesheetError):
            services.log_time(self.junior, other, START, 60, START)

    def test_project_holidays_block_logging(self):
        self.project.holidays.create(on=dt.date(2025, 1, 14))
        with self.assertRaises(services.TimesheetError):
            services.log_time(self.junior, self.item, dt.date(2025, 1, 14), 60, dt.date(2025, 1, 14))

    def test_daily_limit_follows_the_seniority_rule(self):
        limit = rules.max_daily_hours(self.junior.seniority) * 60
        services.log_time(self.junior, self.item, START, limit, START)
        with self.assertRaises(services.DayFull):
            services.log_time(self.junior, self.item, START, 1, START)
        # another person is unaffected
        services.log_time(self.senior, self.item, START, 60, START)

    def test_last_minute_that_fits_is_accepted(self):
        limit = rules.max_daily_hours(self.senior.seniority) * 60
        services.log_time(self.senior, self.item, START, limit - 1, START)
        services.log_time(self.senior, self.item, START, 1, START)
        self.assertEqual(services.minutes_on(self.senior, START), limit)

    def test_week_locking_follows_the_team_size_rule(self):
        cal = project_services.calendar_for(self.project)
        window = rules.timesheet_lock_days(project_services.team_size(self.project))
        services.log_time(self.junior, self.item, START, 60, cal.add(START, window))
        with self.assertRaises(services.WeekLocked):
            services.log_time(self.junior, self.item, START, 60, cal.add(START, window + 1))
        self.assertEqual(TimeEntry.objects.count(), 1)


class WeekSummaryTests(TestCase):
    def setUp(self):
        self.project = make_project()
        self.item = make_items(self.project, {"T1": 5})["T1"]
        self.member = self.project.members.get(seniority=3)

    def fill_week(self, minutes_per_day):
        for i in range(5):
            day = START + dt.timedelta(days=i)
            services.log_time(self.member, self.item, day, minutes_per_day, day)

    def test_week_start_is_monday(self):
        self.assertEqual(services.week_start(dt.date(2025, 1, 17)), START)
        self.assertEqual(services.week_start(dt.date(2025, 1, 19)), START)

    def test_regular_week_costs_the_base_rate(self):
        hours = min(8, rules.max_daily_hours(self.member.seniority))
        self.fill_week(hours * 60)
        summary = services.week_summary(self.member, dt.date(2025, 1, 15))
        self.assertEqual(summary["minutes"], 5 * hours * 60)
        self.assertEqual(summary["cost_cents"], 5 * hours * self.member.hourly_rate_cents)
        self.assertEqual(summary["week_start"], START)

    def test_overtime_week(self):
        self.fill_week(rules.max_daily_hours(3) * 60)
        minutes = services.week_minutes(self.member, START)
        pct = rules.overtime_multiplier_pct(minutes // 60)
        regular = min(minutes, 2400)
        expected = regular * self.member.hourly_rate_cents // 60 + (minutes - regular) * self.member.hourly_rate_cents * pct // 6000
        summary = services.week_summary(self.member, START)
        self.assertEqual(summary["multiplier_pct"], pct)
        self.assertEqual(summary["cost_cents"], expected)

    def test_other_weeks_are_not_counted(self):
        self.fill_week(60)
        later = START + dt.timedelta(days=7)
        services.log_time(self.member, self.item, later, 30, later)
        self.assertEqual(services.week_minutes(self.member, START), 300)
        self.assertEqual(services.week_minutes(self.member, later), 30)
