"""Time-entry limits, week locking and overtime costing."""
from . import rules

REGULAR_WEEK_MINUTES = 40 * 60


def daily_limit_minutes(seniority):
    return rules.max_daily_hours(seniority) * 60


def day_has_room(seniority, logged_minutes, new_minutes):
    return logged_minutes + new_minutes <= daily_limit_minutes(seniority)


def lock_window_days(team_size):
    return rules.timesheet_lock_days(team_size)


def is_locked(calendar, worked_on, today, team_size):
    """An entry can no longer change once more working days than the lock window have passed."""
    return calendar.between(worked_on, today) > lock_window_days(team_size)


def overtime_multiplier_pct(weekly_minutes):
    return rules.overtime_multiplier_pct(weekly_minutes // 60)


def weekly_cost_cents(weekly_minutes, rate_cents_per_hour):
    """Pay for a week: regular minutes at the base rate, the rest at the multiplier for the week's total hours."""
    regular = min(weekly_minutes, REGULAR_WEEK_MINUTES)
    over = weekly_minutes - regular
    cost = regular * rate_cents_per_hour // 60
    if over:
        cost += over * rate_cents_per_hour * overtime_multiplier_pct(weekly_minutes) // 6000
    return cost
