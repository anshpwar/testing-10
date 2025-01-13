"""Milestone health: forecast slip against tolerance and baseline freeze windows."""
from . import rules

ON_TRACK, AT_RISK, LATE = "on_track", "at_risk", "late"


def slip_days(calendar, due, forecast):
    """Working days the forecast finish is later than the due date (zero or negative when early)."""
    return calendar.between(due, forecast)


def slip_tolerance(duration_days):
    return rules.milestone_slip_tolerance_days(duration_days)


def slip_status(calendar, due, forecast, duration_days):
    slip = slip_days(calendar, due, forecast)
    if slip <= 0:
        return ON_TRACK
    if slip <= slip_tolerance(duration_days):
        return AT_RISK
    return LATE


def freeze_days(duration_days):
    return rules.baseline_freeze_days(duration_days)


def baseline_locked(calendar, today, baseline_due, duration_days):
    """A baseline cannot be changed once it is within its freeze window of working days before the due date."""
    return calendar.between(today, baseline_due) <= freeze_days(duration_days)
