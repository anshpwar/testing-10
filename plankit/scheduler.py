"""Turns a task graph into dated schedules using the working calendar and the risk-reserve policy."""
from dataclasses import dataclass, field

from . import critical, rules


@dataclass(frozen=True)
class Scheduled:
    code: str
    start: object
    finish: object
    es: int
    ef: int
    slack: int
    critical: bool


@dataclass
class Plan:
    tasks: dict
    length_days: int
    finish: object
    reserve_days: int
    committed_finish: object
    critical_path: list = field(default_factory=list)
    near_critical: list = field(default_factory=list)

    def window(self, code):
        item = self.tasks[code]
        return item.start, item.finish


def reserve_days(length_days, dependency_count):
    """Working days of schedule reserve held back for a plan of the given length and coupling."""
    pct = rules.risk_reserve_pct(dependency_count)
    return -(-length_days * pct // 100)


def plan(graph, start, calendar, not_before=None, extra_days=None):
    """Schedule every task as early as its prerequisites and `not_before` dates allow.

    `extra_days` adds working days to named tasks, which is how what-if analyses are run.
    """
    first = calendar.next_workday(start)
    if extra_days:
        graph = _stretched(graph, extra_days)
    floors = {}
    for code, date in (not_before or {}).items():
        if date > first:
            floors[code] = calendar.between(first, calendar.next_workday(date))
    timings = critical.analyse(graph, floors)
    length = critical.project_length(timings)
    scheduled = {}
    for code, t in timings.items():
        scheduled[code] = Scheduled(code, calendar.add(first, t.es), calendar.add(first, t.ef - 1),
                                    t.es, t.ef, t.slack, t.critical)
    if length:
        finish = calendar.add(first, length - 1)
    else:
        finish = first
    reserve = reserve_days(length, graph.edge_count())
    committed = calendar.add(finish, reserve) if reserve else finish
    return Plan(
        tasks=scheduled,
        length_days=length,
        finish=finish,
        reserve_days=reserve,
        committed_finish=committed,
        critical_path=critical.critical_path(graph, timings),
        near_critical=critical.near_critical(timings, rules.critical_slack_days(length)),
    )


def _stretched(graph, extra_days):
    from .depgraph import TaskGraph

    out = TaskGraph()
    for code in graph.tasks():
        out.add_task(code, graph.duration(code) + extra_days.get(code, 0))
    for code in graph.tasks():
        for dep in graph.dependencies(code):
            out.add_dependency(code, dep)
    return out


def slip_of(base, changed):
    """Working days by which `changed` finishes after `base` (both Plans on the same calendar and start)."""
    return changed.length_days - base.length_days
