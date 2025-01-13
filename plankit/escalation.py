"""Escalation of stalled assignments by task priority."""
from . import rules

PRIORITIES = (1, 2, 3, 4)


def escalation_after(priority):
    return rules.escalation_after_days(priority)


def is_due(calendar, assigned_on, today, priority):
    """True once the assignment has been open for the priority's number of working days."""
    return calendar.between(assigned_on, today) >= escalation_after(priority)


def due_date(calendar, assigned_on, priority):
    return calendar.add(assigned_on, escalation_after(priority))


def overdue_by(calendar, assigned_on, today, priority):
    return max(calendar.between(assigned_on, today) - escalation_after(priority), 0)
