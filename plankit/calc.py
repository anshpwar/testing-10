"""Composite charges built from the policy tables."""
from . import rules


def combined_charge(x):
    """Total of the two base schedules for x."""
    return rules.task_buffer_pct(x) + rules.review_turnaround_hours(x)
