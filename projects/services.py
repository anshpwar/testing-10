"""Project planning: calendars, dependency graphs and persisted schedules. Timing policy comes from plankit."""
from plankit import cadence, capacity
from plankit.depgraph import CycleError, GraphError, TaskGraph
from plankit.scheduler import plan as build_plan
from plankit.workcal import WorkCalendar

from .models import Dependency, Holiday, Project, WorkItem


class ProjectError(Exception):
    pass


def team_size(project):
    return project.members.filter(active=True).count()


def calendar_for(project):
    return WorkCalendar(project.workweek, [h.on for h in project.holidays.all()])


def create_item(project, code, title, duration_days, priority=2, not_before=None):
    if duration_days < 1:
        raise ProjectError("duration must be at least one working day")
    if WorkItem.objects.filter(project=project, code=code).exists():
        raise ProjectError(f"{code} already exists")
    return WorkItem.objects.create(project=project, code=code, title=title, duration_days=duration_days,
                                   priority=priority, not_before=not_before)


def build_graph(project):
    graph = TaskGraph()
    items = list(project.items.all())
    for item in items:
        graph.add_task(item.code, item.duration_days)
    by_id = {item.id: item.code for item in items}
    for dep in Dependency.objects.filter(item__project=project):
        graph.add_dependency(by_id[dep.item_id], by_id[dep.depends_on_id])
    return graph


def add_dependency(item, depends_on):
    """Record that `item` cannot start before `depends_on` finishes; refuses anything that would loop."""
    if item.project_id != depends_on.project_id:
        raise ProjectError("dependencies must stay inside one project")
    graph = build_graph(item.project)
    if graph.would_cycle(item.code, depends_on.code):
        raise ProjectError(f"{item.code} -> {depends_on.code} would create a cycle")
    return Dependency.objects.get_or_create(item=item, depends_on=depends_on)[0]


def schedule(project, persist=True):
    """Compute the plan and, unless told otherwise, store planned dates on the items."""
    try:
        graph = build_graph(project)
        floors = {i.code: i.not_before for i in project.items.exclude(not_before=None)}
        result = build_plan(graph, project.start_on, calendar_for(project), floors)
    except (CycleError, GraphError) as exc:
        raise ProjectError(str(exc)) from exc
    if persist:
        for item in project.items.all():
            window = result.window(item.code)
            item.planned_start, item.planned_finish = window
            item.save(update_fields=["planned_start", "planned_finish"])
    return result


def duration_days(project):
    """Planned length of the project in working days (zero while nothing is scheduled)."""
    return schedule(project, persist=False).length_days


def sprint_windows(project, count):
    return cadence.sprint_windows(project.start_on, calendar_for(project), max(team_size(project), 1), count)


def capacity_between(project, start, end):
    return capacity.person_days(calendar_for(project), start, end, team_size(project))


def status_counts(project):
    out = {WorkItem.TODO: 0, WorkItem.DOING: 0, WorkItem.DONE: 0}
    for item in project.items.all():
        out[item.status] += 1
    return out
