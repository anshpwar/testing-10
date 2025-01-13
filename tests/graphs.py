"""Plain task graphs shared by the scheduler tests (no Django needed)."""
from plankit.depgraph import TaskGraph


def build(durations, links=()):
    g = TaskGraph()
    for code, days in durations.items():
        g.add_task(code, days)
    for task, dep in links:
        g.add_dependency(task, dep)
    return g


def diamond():
    """A(3) feeds B(2) and C(4), which both feed D(1): critical chain A-C-D, B has two days of slack."""
    return build({"A": 3, "B": 2, "C": 4, "D": 1}, [("B", "A"), ("C", "A"), ("D", "B"), ("D", "C")])


def two_tracks():
    """Two independent chains of different length that join in a final task."""
    return build({"P1": 2, "P2": 2, "Q1": 5, "R": 1}, [("P2", "P1"), ("R", "P2"), ("R", "Q1")])
