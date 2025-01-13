"""Team capacity: person-days available, work-in-progress limits and assignment caps."""
from . import rules


def holiday_cover_pct(team_size):
    return rules.holiday_cover_pct(team_size)


def person_days(calendar, start, end, team_size):
    """Person-days of effort in [start, end) after holding back the holiday and absence cover."""
    days = calendar.between(start, end)
    gross = days * team_size
    return gross - -(-gross * holiday_cover_pct(team_size) // 100)


def wip_limit(team_size):
    return rules.wip_limit(team_size)


def wip_available(team_size, in_progress):
    return max(wip_limit(team_size) - in_progress, 0)


def assignment_cap(seniority):
    return rules.max_assignments_per_person(seniority)


def assignment_room(seniority, current):
    return max(assignment_cap(seniority) - current, 0)


def utilisation_pct(planned_days, capacity_days):
    if capacity_days <= 0:
        return 0 if planned_days == 0 else 999
    return planned_days * 100 // capacity_days
