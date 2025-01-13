"""Milestone forecasting and baselines. Slip tolerance and freeze windows come from plankit.health."""
from plankit import health
from projects import services as project_services

from .models import Milestone


class MilestoneError(Exception):
    pass


def forecast_finish(milestone):
    """Latest planned finish among the milestone's items (items must have been scheduled)."""
    dates = [i.planned_finish for i in milestone.items.all() if i.planned_finish]
    if not dates:
        raise MilestoneError("milestone has no scheduled items")
    return max(dates)


def span_days(milestone):
    """Working days from the project start to the milestone due date."""
    project = milestone.project
    return max(project_services.calendar_for(project).between(project.start_on, milestone.due_on), 0)


def status(milestone):
    project = milestone.project
    calendar = project_services.calendar_for(project)
    return health.slip_status(calendar, milestone.due_on, forecast_finish(milestone), span_days(milestone))


def slip(milestone):
    calendar = project_services.calendar_for(milestone.project)
    return health.slip_days(calendar, milestone.due_on, forecast_finish(milestone))


def baseline_is_locked(milestone, today):
    if milestone.baseline_due_on is None:
        return False
    calendar = project_services.calendar_for(milestone.project)
    return health.baseline_locked(calendar, today, milestone.baseline_due_on, span_days(milestone))


def set_baseline(milestone, today):
    """Record the current due date as the baseline, unless an existing baseline is inside its freeze window."""
    if baseline_is_locked(milestone, today):
        raise MilestoneError("baseline is frozen")
    milestone.baseline_due_on = milestone.due_on
    milestone.save(update_fields=["baseline_due_on"])
    return milestone


def move_due_date(milestone, new_due, today):
    if baseline_is_locked(milestone, today):
        raise MilestoneError("baseline is frozen")
    milestone.due_on = new_due
    milestone.save(update_fields=["due_on"])
    return milestone


def rollup(project):
    """Status of every milestone of a project that already has a forecast."""
    out = {}
    for milestone in Milestone.objects.filter(project=project):
        try:
            out[milestone.name] = status(milestone)
        except MilestoneError:
            out[milestone.name] = "unscheduled"
    return out
