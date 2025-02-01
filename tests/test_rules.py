import unittest

from plankit import rules


class RuleTests(unittest.TestCase):
    def test_task_buffer_pct(self):
        self.assertEqual(rules.task_buffer_pct(0), 10)
        self.assertEqual(rules.task_buffer_pct(1), 10)
        self.assertEqual(rules.task_buffer_pct(3), 10)
        self.assertEqual(rules.task_buffer_pct(4), 20)
        self.assertEqual(rules.task_buffer_pct(10), 20)
        self.assertEqual(rules.task_buffer_pct(11), 30)
        self.assertEqual(rules.task_buffer_pct(30), 30)
        self.assertEqual(rules.task_buffer_pct(31), 40)

    def test_review_turnaround_hours(self):
        self.assertEqual(rules.review_turnaround_hours(0), 4)
        self.assertEqual(rules.review_turnaround_hours(1), 4)
        self.assertEqual(rules.review_turnaround_hours(50), 4)
        self.assertEqual(rules.review_turnaround_hours(51), 8)
        self.assertEqual(rules.review_turnaround_hours(200), 8)
        self.assertEqual(rules.review_turnaround_hours(201), 24)
        self.assertEqual(rules.review_turnaround_hours(1000), 24)
        self.assertEqual(rules.review_turnaround_hours(1001), 48)

    def test_max_daily_hours(self):
        self.assertEqual(rules.max_daily_hours(0), 6)
        self.assertEqual(rules.max_daily_hours(1), 6)
        self.assertEqual(rules.max_daily_hours(2), 6)
        self.assertEqual(rules.max_daily_hours(3), 7)
        self.assertEqual(rules.max_daily_hours(4), 8)

    def test_overtime_multiplier_pct(self):
        self.assertEqual(rules.overtime_multiplier_pct(0), 100)
        self.assertEqual(rules.overtime_multiplier_pct(1), 100)
        self.assertEqual(rules.overtime_multiplier_pct(40), 100)
        self.assertEqual(rules.overtime_multiplier_pct(41), 150)
        self.assertEqual(rules.overtime_multiplier_pct(50), 150)
        self.assertEqual(rules.overtime_multiplier_pct(51), 175)
        self.assertEqual(rules.overtime_multiplier_pct(60), 175)
        self.assertEqual(rules.overtime_multiplier_pct(61), 200)

    def test_milestone_slip_tolerance_days(self):
        self.assertEqual(rules.milestone_slip_tolerance_days(0), 1)
        self.assertEqual(rules.milestone_slip_tolerance_days(1), 1)
        self.assertEqual(rules.milestone_slip_tolerance_days(14), 1)
        self.assertEqual(rules.milestone_slip_tolerance_days(15), 1)
        self.assertEqual(rules.milestone_slip_tolerance_days(60), 3)
        self.assertEqual(rules.milestone_slip_tolerance_days(61), 3)
        self.assertEqual(rules.milestone_slip_tolerance_days(180), 7)
        self.assertEqual(rules.milestone_slip_tolerance_days(181), 7)

    def test_wip_limit(self):
        self.assertEqual(rules.wip_limit(0), 2)
        self.assertEqual(rules.wip_limit(1), 2)
        self.assertEqual(rules.wip_limit(3), 2)
        self.assertEqual(rules.wip_limit(4), 4)
        self.assertEqual(rules.wip_limit(6), 4)
        self.assertEqual(rules.wip_limit(7), 7)
        self.assertEqual(rules.wip_limit(12), 7)
        self.assertEqual(rules.wip_limit(13), 10)

    def test_escalation_after_days(self):
        self.assertEqual(rules.escalation_after_days(0), 1)
        self.assertEqual(rules.escalation_after_days(1), 1)
        self.assertEqual(rules.escalation_after_days(2), 3)
        self.assertEqual(rules.escalation_after_days(3), 5)
        self.assertEqual(rules.escalation_after_days(4), 10)

    def test_max_assignments_per_person(self):
        self.assertEqual(rules.max_assignments_per_person(0), 3)
        self.assertEqual(rules.max_assignments_per_person(1), 3)
        self.assertEqual(rules.max_assignments_per_person(2), 4)
        self.assertEqual(rules.max_assignments_per_person(3), 5)
        self.assertEqual(rules.max_assignments_per_person(4), 6)

    def test_standup_minutes(self):
        self.assertEqual(rules.standup_minutes(0), 10)
        self.assertEqual(rules.standup_minutes(1), 10)
        self.assertEqual(rules.standup_minutes(4), 10)
        self.assertEqual(rules.standup_minutes(5), 15)
        self.assertEqual(rules.standup_minutes(8), 15)
        self.assertEqual(rules.standup_minutes(9), 20)
        self.assertEqual(rules.standup_minutes(15), 20)
        self.assertEqual(rules.standup_minutes(16), 30)

    def test_risk_reserve_pct(self):
        self.assertEqual(rules.risk_reserve_pct(0), 5)
        self.assertEqual(rules.risk_reserve_pct(1), 5)
        self.assertEqual(rules.risk_reserve_pct(2), 5)
        self.assertEqual(rules.risk_reserve_pct(3), 10)
        self.assertEqual(rules.risk_reserve_pct(5), 10)
        self.assertEqual(rules.risk_reserve_pct(6), 20)
        self.assertEqual(rules.risk_reserve_pct(10), 20)
        self.assertEqual(rules.risk_reserve_pct(11), 30)

    def test_timesheet_lock_days(self):
        self.assertEqual(rules.timesheet_lock_days(0), 7)
        self.assertEqual(rules.timesheet_lock_days(1), 7)
        self.assertEqual(rules.timesheet_lock_days(5), 7)
        self.assertEqual(rules.timesheet_lock_days(6), 5)
        self.assertEqual(rules.timesheet_lock_days(15), 5)
        self.assertEqual(rules.timesheet_lock_days(16), 3)
        self.assertEqual(rules.timesheet_lock_days(50), 3)
        self.assertEqual(rules.timesheet_lock_days(51), 2)

    def test_sprint_length_days(self):
        self.assertEqual(rules.sprint_length_days(0), 5)
        self.assertEqual(rules.sprint_length_days(1), 5)
        self.assertEqual(rules.sprint_length_days(5), 5)
        self.assertEqual(rules.sprint_length_days(6), 10)
        self.assertEqual(rules.sprint_length_days(10), 10)
        self.assertEqual(rules.sprint_length_days(11), 14)
        self.assertEqual(rules.sprint_length_days(20), 14)
        self.assertEqual(rules.sprint_length_days(21), 21)

    def test_critical_slack_days(self):
        self.assertEqual(rules.critical_slack_days(0), 0)
        self.assertEqual(rules.critical_slack_days(1), 0)
        self.assertEqual(rules.critical_slack_days(30), 0)
        self.assertEqual(rules.critical_slack_days(31), 0)
        self.assertEqual(rules.critical_slack_days(90), 2)
        self.assertEqual(rules.critical_slack_days(91), 2)
        self.assertEqual(rules.critical_slack_days(180), 5)
        self.assertEqual(rules.critical_slack_days(181), 5)

    def test_holiday_cover_pct(self):
        self.assertEqual(rules.holiday_cover_pct(0), 5)
        self.assertEqual(rules.holiday_cover_pct(1), 5)
        self.assertEqual(rules.holiday_cover_pct(3), 5)
        self.assertEqual(rules.holiday_cover_pct(4), 8)
        self.assertEqual(rules.holiday_cover_pct(8), 8)
        self.assertEqual(rules.holiday_cover_pct(9), 12)
        self.assertEqual(rules.holiday_cover_pct(20), 12)
        self.assertEqual(rules.holiday_cover_pct(21), 15)

    def test_baseline_freeze_days(self):
        self.assertEqual(rules.baseline_freeze_days(0), 3)
        self.assertEqual(rules.baseline_freeze_days(1), 3)
        self.assertEqual(rules.baseline_freeze_days(30), 3)
        self.assertEqual(rules.baseline_freeze_days(31), 3)
        self.assertEqual(rules.baseline_freeze_days(90), 7)
        self.assertEqual(rules.baseline_freeze_days(91), 7)
        self.assertEqual(rules.baseline_freeze_days(180), 14)
        self.assertEqual(rules.baseline_freeze_days(181), 14)

    def test_estimate_confidence_pct(self):
        self.assertEqual(rules.estimate_confidence_pct(0), 90)
        self.assertEqual(rules.estimate_confidence_pct(1), 90)
        self.assertEqual(rules.estimate_confidence_pct(5), 90)
        self.assertEqual(rules.estimate_confidence_pct(6), 80)
        self.assertEqual(rules.estimate_confidence_pct(20), 80)
        self.assertEqual(rules.estimate_confidence_pct(21), 70)
        self.assertEqual(rules.estimate_confidence_pct(60), 70)
        self.assertEqual(rules.estimate_confidence_pct(61), 60)
