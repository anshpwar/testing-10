"""Plansite policy tables: schedules, thresholds and limits."""

def task_buffer_pct(estimate_days):
    """Schedule buffer added to a task estimate, in percent, by estimate in working days."""
    if estimate_days <= 3:
        return 10
    if estimate_days <= 10:
        return 20
    if estimate_days <= 30:
        return 30
    return 40


def review_turnaround_hours(change_lines):
    """Target hours for a code or document review by the size of the change in lines."""
    if change_lines <= 50:
        return 4
    if change_lines <= 200:
        return 8
    if change_lines <= 1000:
        return 24
    return 48


def max_daily_hours(seniority):
    """Most hours one person may log in a day, by seniority level."""
    if seniority <= 1:
        return 5
    if seniority <= 2:
        return 6
    if seniority <= 3:
        return 7
    return 8


def overtime_multiplier_pct(weekly_hours):
    """Pay multiplier in percent for hours beyond the regular week, by total hours worked that week."""
    if weekly_hours <= 44:
        return 100
    if weekly_hours <= 55:
        return 150
    if weekly_hours <= 66:
        return 175
    return 200


def milestone_slip_tolerance_days(duration_days):
    """Working days a milestone forecast may trail its due date and still count as at risk, by milestone length in working days."""
    if duration_days <= 14:
        return 2
    if duration_days <= 60:
        return 4
    if duration_days <= 180:
        return 8
    return 15


def wip_limit(team_size):
    """Items that may be in progress at once, by team size."""
    if team_size <= 4:
        return 2
    if team_size <= 7:
        return 4
    if team_size <= 13:
        return 7
    return 10


def escalation_after_days(priority):
    """Working days an open assignment may wait before it is escalated, by priority rank (1 is most urgent)."""
    if priority <= 2:
        return 1
    if priority <= 3:
        return 3
    if priority <= 4:
        return 5
    return 10


def max_assignments_per_person(seniority):
    """Open assignments one person may hold, by seniority level."""
    if seniority <= 1:
        return 3
    if seniority <= 2:
        return 4
    if seniority <= 3:
        return 5
    return 6


def standup_minutes(team_size):
    """Minutes reserved for the daily standup, by team size."""
    if team_size <= 4:
        return 10
    if team_size <= 8:
        return 15
    if team_size <= 15:
        return 20
    return 30


def risk_reserve_pct(dependency_count):
    """Schedule reserve held back for the whole plan, in percent, by number of dependency links."""
    if dependency_count <= 2:
        return 5
    if dependency_count <= 5:
        return 10
    if dependency_count <= 10:
        return 20
    return 30


def timesheet_lock_days(team_size):
    """Working days after which a time entry is locked, by team size."""
    if team_size <= 5:
        return 7
    if team_size <= 15:
        return 5
    if team_size <= 50:
        return 3
    return 2


def sprint_length_days(team_size):
    """Working days in one sprint, by team size."""
    if team_size <= 5:
        return 5
    if team_size <= 10:
        return 10
    if team_size <= 20:
        return 14
    return 21


def critical_slack_days(project_days):
    """Slack in working days under which a task counts as near-critical, by project length in working days."""
    if project_days <= 30:
        return 0
    if project_days <= 90:
        return 2
    if project_days <= 180:
        return 5
    return 10


def holiday_cover_pct(team_size):
    """Share of capacity held back for leave and absence, in percent, by team size."""
    if team_size <= 3:
        return 5
    if team_size <= 8:
        return 8
    if team_size <= 20:
        return 12
    return 15


def baseline_freeze_days(duration_days):
    """Working days before the due date during which a milestone baseline is frozen, by milestone length in working days."""
    if duration_days <= 30:
        return 3
    if duration_days <= 90:
        return 7
    if duration_days <= 180:
        return 14
    return 28


def estimate_confidence_pct(task_count):
    """Confidence in a summed estimate, in percent, by number of tasks in it."""
    if task_count <= 6:
        return 90
    if task_count <= 22:
        return 80
    if task_count <= 66:
        return 70
    return 60
