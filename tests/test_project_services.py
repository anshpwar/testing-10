import datetime as dt

from django.test import TestCase

from plankit import cadence, rules
from projects import services
from projects.models import Dependency, WorkItem

from .factories import DIAMOND, START, make_items, make_project


class ItemTests(TestCase):
    def setUp(self):
        self.project = make_project()

    def test_create_item(self):
        item = services.create_item(self.project, "T1", "First", 3, priority=1)
        self.assertEqual((item.code, item.duration_days, item.priority, item.status), ("T1", 3, 1, WorkItem.TODO))
        self.assertEqual(str(item), "ATLAS-T1")

    def test_duplicate_code_and_zero_duration_are_rejected(self):
        services.create_item(self.project, "T1", "First", 3)
        with self.assertRaises(services.ProjectError):
            services.create_item(self.project, "T1", "Again", 2)
        with self.assertRaises(services.ProjectError):
            services.create_item(self.project, "T2", "Empty", 0)

    def test_team_size_counts_active_members_only(self):
        self.assertEqual(services.team_size(self.project), 3)
        member = self.project.members.first()
        member.active = False
        member.save()
        self.assertEqual(services.team_size(self.project), 2)

    def test_status_counts(self):
        items = make_items(self.project, {"A": 1, "B": 1, "C": 1})
        items["B"].status = WorkItem.DOING
        items["B"].save()
        self.assertEqual(services.status_counts(self.project), {"todo": 2, "doing": 1, "done": 0})


class DependencyTests(TestCase):
    def setUp(self):
        self.project = make_project()
        self.items = make_items(self.project, *DIAMOND)

    def test_graph_matches_the_stored_links(self):
        graph = services.build_graph(self.project)
        self.assertEqual(graph.order(), ["A", "B", "C", "D"])
        self.assertEqual(graph.dependencies("D"), ["B", "C"])

    def test_add_dependency_is_idempotent(self):
        services.add_dependency(self.items["B"], self.items["A"])
        services.add_dependency(self.items["B"], self.items["A"])
        self.assertEqual(Dependency.objects.filter(item=self.items["B"]).count(), 1)

    def test_loops_are_refused(self):
        with self.assertRaises(services.ProjectError):
            services.add_dependency(self.items["A"], self.items["D"])
        with self.assertRaises(services.ProjectError):
            services.add_dependency(self.items["A"], self.items["A"])
        self.assertEqual(Dependency.objects.count(), 4)

    def test_other_projects_are_refused(self):
        other = make_items(make_project("ORBIT"), {"X": 1})
        with self.assertRaises(services.ProjectError):
            services.add_dependency(self.items["A"], other["X"])


class ScheduleTests(TestCase):
    def setUp(self):
        self.project = make_project()
        self.items = make_items(self.project, *DIAMOND)

    def test_schedule_persists_planned_dates(self):
        result = services.schedule(self.project)
        self.assertEqual(result.length_days, 8)
        for item in WorkItem.objects.filter(project=self.project):
            self.assertEqual((item.planned_start, item.planned_finish), result.window(item.code))
        d = WorkItem.objects.get(project=self.project, code="D")
        self.assertEqual(d.planned_finish, dt.date(2025, 1, 22))

    def test_schedule_without_persisting(self):
        services.schedule(self.project, persist=False)
        self.assertIsNone(WorkItem.objects.get(project=self.project, code="A").planned_start)

    def test_project_holidays_move_the_plan(self):
        self.project.holidays.create(on=dt.date(2025, 1, 16))
        result = services.schedule(self.project, persist=False)
        self.assertEqual(result.finish, dt.date(2025, 1, 23))

    def test_custom_workweek(self):
        self.project.workweek = 0b0001111  # Monday to Thursday
        self.project.save()
        result = services.schedule(self.project, persist=False)
        self.assertEqual(result.finish, dt.date(2025, 1, 23))
        self.assertEqual(services.duration_days(self.project), 8)

    def test_not_before_floor_is_honoured(self):
        WorkItem.objects.filter(project=self.project, code="D").update(not_before=dt.date(2025, 2, 3))
        result = services.schedule(self.project, persist=False)
        self.assertEqual(result.window("D")[0], dt.date(2025, 2, 3))

    def test_cycle_in_stored_data_is_reported(self):
        Dependency.objects.create(item=self.items["A"], depends_on=self.items["D"])
        with self.assertRaises(services.ProjectError):
            services.schedule(self.project)

    def test_sprint_windows_use_team_size(self):
        windows = services.sprint_windows(self.project, 2)
        self.assertEqual(windows, cadence.sprint_windows(START, services.calendar_for(self.project), 3, 2))
        first, last = windows[0]
        self.assertEqual(services.calendar_for(self.project).between(first, last + dt.timedelta(days=1)),
                         rules.sprint_length_days(3))

    def test_capacity_between(self):
        end = dt.date(2025, 1, 27)
        gross = 10 * 3
        cover = rules.holiday_cover_pct(3)
        self.assertEqual(services.capacity_between(self.project, START, end), gross - -(-gross * cover // 100))
