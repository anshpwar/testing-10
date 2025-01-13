"""Sprint windows and meeting load derived from team size and the working calendar."""
from . import rules


def sprint_length(team_size):
    return rules.sprint_length_days(team_size)


def sprint_windows(start, calendar, team_size, count):
    """`count` back-to-back sprints, each exactly one sprint length of working days; returns (first, last) pairs."""
    length = sprint_length(team_size)
    windows = []
    first = calendar.next_workday(start)
    for _ in range(count):
        last = calendar.add(first, length - 1)
        windows.append((first, last))
        first = calendar.add(last, 1)
    return windows


def sprint_index(windows, date):
    """Zero-based index of the sprint containing `date`, or None for a date outside every window."""
    for i, (first, last) in enumerate(windows):
        if first <= date <= last:
            return i
    return None


def standup_minutes_per_sprint(team_size):
    return rules.standup_minutes(team_size) * sprint_length(team_size)


def meeting_share_pct(team_size, workday_minutes=480):
    """Share of a working day, in whole percent, that goes to the daily standup."""
    return rules.standup_minutes(team_size) * 100 // workday_minutes
