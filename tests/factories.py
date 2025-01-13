"""Small builders shared by the Django tests. Dates are fixed so every test is deterministic."""
import datetime as dt

from projects.models import Dependency, Member, Project, WorkItem

START = dt.date(2025, 1, 13)  # a Monday


def make_project(key="ATLAS", start=START, members=3, holidays=()):
    project = Project.objects.create(key=key, name=f"{key} rollout", start_on=start)
    for i in range(members):
        Member.objects.create(project=project, name=f"Member {i + 1}", seniority=i + 1)
    for day in holidays:
        project.holidays.create(on=day)
    return project


def make_items(project, spec, links=()):
    """spec: {code: duration}; links: (code, depends_on) pairs. Returns {code: WorkItem}."""
    items = {code: WorkItem.objects.create(project=project, code=code, title=f"Item {code}", duration_days=days)
             for code, days in spec.items()}
    for code, needs in links:
        Dependency.objects.create(item=items[code], depends_on=items[needs])
    return items


DIAMOND = ({"A": 3, "B": 2, "C": 4, "D": 1}, [("B", "A"), ("C", "A"), ("D", "B"), ("D", "C")])
