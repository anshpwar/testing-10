"""Assigning people to work items, within per-person caps and the project's work-in-progress limit."""
from plankit import capacity, escalation
from projects import services as project_services
from projects.models import WorkItem

from .models import Assignment


class AssignmentError(Exception):
    pass


class PersonOverloaded(AssignmentError):
    pass


class WipLimitReached(AssignmentError):
    pass


def open_count(member):
    return Assignment.objects.filter(member=member, state=Assignment.ASSIGNED).count()


def doing_count(project):
    return project.items.filter(status=WorkItem.DOING).count()


def assign(item, member, today, hours=8):
    """Give `item` to `member`; the first assignment of a todo item starts it, which counts against the WIP limit."""
    if member.project_id != item.project_id:
        raise AssignmentError("member and item belong to different projects")
    if not member.active:
        raise AssignmentError("member is not active")
    if item.status == WorkItem.DONE:
        raise AssignmentError("item is already done")
    if Assignment.objects.filter(item=item, member=member, state=Assignment.ASSIGNED).exists():
        raise AssignmentError("already assigned")
    if capacity.assignment_room(member.seniority, open_count(member)) == 0:
        raise PersonOverloaded(f"{member.name} is at the assignment cap")
    if item.status == WorkItem.TODO:
        team = max(project_services.team_size(item.project), 1)
        if capacity.wip_available(team, doing_count(item.project)) == 0:
            raise WipLimitReached("work-in-progress limit reached")
        item.status = WorkItem.DOING
        item.save(update_fields=["status"])
    return Assignment.objects.create(item=item, member=member, assigned_on=today, hours_planned=hours)


def release(assignment):
    assignment.state = Assignment.RELEASED
    assignment.save(update_fields=["state"])
    still_open = Assignment.objects.filter(item=assignment.item, state=Assignment.ASSIGNED).exists()
    if not still_open and assignment.item.status == WorkItem.DOING:
        assignment.item.status = WorkItem.TODO
        assignment.item.save(update_fields=["status"])
    return assignment


def due_for_escalation(project, today):
    """Open assignments that have waited at least the priority's escalation period, oldest first."""
    calendar = project_services.calendar_for(project)
    rows = Assignment.objects.filter(item__project=project, state=Assignment.ASSIGNED, escalated_on=None)
    return [a for a in rows.select_related("item")
            if escalation.is_due(calendar, a.assigned_on, today, a.item.priority)]


def escalate(project, today):
    due = due_for_escalation(project, today)
    for assignment in due:
        assignment.escalated_on = today
        assignment.save(update_fields=["escalated_on"])
    return due


def load_by_member(project):
    return {m.name: open_count(m) for m in project.members.filter(active=True)}
