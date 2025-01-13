"""Time entries: daily limits by seniority, week locking by team size and weekly costing with overtime."""
import datetime as dt

from django.db.models import Sum

from plankit import timecost
from projects import services as project_services

from .models import TimeEntry


class TimesheetError(Exception):
    pass


class DayFull(TimesheetError):
    pass


class WeekLocked(TimesheetError):
    pass


def minutes_on(member, day):
    return TimeEntry.objects.filter(member=member, worked_on=day).aggregate(total=Sum("minutes"))["total"] or 0


def log_time(member, item, worked_on, minutes, today, note=""):
    if minutes < 1:
        raise TimesheetError("minutes must be positive")
    if item.project_id != member.project_id:
        raise TimesheetError("member and item belong to different projects")
    project = member.project
    calendar = project_services.calendar_for(project)
    if not calendar.is_workday(worked_on):
        raise TimesheetError("time can only be logged on working days")
    if worked_on > today:
        raise TimesheetError("cannot log time in the future")
    team = max(project_services.team_size(project), 1)
    if timecost.is_locked(calendar, worked_on, today, team):
        raise WeekLocked("the entry date is locked")
    if not timecost.day_has_room(member.seniority, minutes_on(member, worked_on), minutes):
        raise DayFull("daily limit reached")
    return TimeEntry.objects.create(member=member, item=item, worked_on=worked_on, minutes=minutes, note=note)


def week_start(day):
    return day - dt.timedelta(days=day.weekday())


def week_minutes(member, day):
    start = week_start(day)
    total = TimeEntry.objects.filter(member=member, worked_on__gte=start, worked_on__lt=start + dt.timedelta(days=7))
    return total.aggregate(total=Sum("minutes"))["total"] or 0


def week_summary(member, day):
    minutes = week_minutes(member, day)
    return {
        "week_start": week_start(day),
        "minutes": minutes,
        "multiplier_pct": timecost.overtime_multiplier_pct(minutes),
        "cost_cents": timecost.weekly_cost_cents(minutes, member.hourly_rate_cents),
    }


def item_minutes(item):
    return TimeEntry.objects.filter(item=item).aggregate(total=Sum("minutes"))["total"] or 0
