import datetime as dt

from django.test import TestCase

from assignments import services
from assignments.models import Assignment
from plankit import rules
from projects import services as project_services
from projects.models import WorkItem

from .factories import START, make_items, make_project


class AssignTests(TestCase):
    def setUp(self):
        self.project = make_project()
        self.members = list(self.project.members.order_by("seniority"))
        self.items = make_items(self.project, {f"T{i}": 2 for i in range(1, 9)})

    def test_first_assignment_starts_the_item(self):
        a = services.assign(self.items["T1"], self.members[0], START)
        self.assertEqual(a.state, Assignment.ASSIGNED)
        self.items["T1"].refresh_from_db()
        self.assertEqual(self.items["T1"].status, WorkItem.DOING)

    def test_second_person_on_a_doing_item(self):
        services.assign(self.items["T1"], self.members[0], START)
        services.assign(self.items["T1"], self.members[1], START)
        self.assertEqual(services.doing_count(self.project), 1)

    def test_duplicate_and_foreign_assignments_are_rejected(self):
        services.assign(self.items["T1"], self.members[0], START)
        with self.assertRaises(services.AssignmentError):
            services.assign(self.items["T1"], self.members[0], START)
        other = make_project("ORBIT")
        with self.assertRaises(services.AssignmentError):
            services.assign(self.items["T2"], other.members.first(), START)

    def test_inactive_member_and_done_item(self):
        self.members[0].active = False
        self.members[0].save()
        with self.assertRaises(services.AssignmentError):
            services.assign(self.items["T1"], self.members[0], START)
        self.items["T2"].status = WorkItem.DONE
        self.items["T2"].save()
        with self.assertRaises(services.AssignmentError):
            services.assign(self.items["T2"], self.members[1], START)

    def test_person_cap_follows_the_seniority_rule(self):
        member = self.members[0]
        cap = rules.max_assignments_per_person(member.seniority)
        WorkItem.objects.filter(project=self.project).update(status=WorkItem.DOING)
        codes = [f"T{i}" for i in range(1, 9)]
        for code in codes[:cap]:
            services.assign(WorkItem.objects.get(project=self.project, code=code), member, START)
        with self.assertRaises(services.PersonOverloaded):
            services.assign(WorkItem.objects.get(project=self.project, code=codes[cap]), member, START)
        self.assertEqual(services.open_count(member), cap)

    def test_wip_limit_follows_the_team_size_rule(self):
        limit = rules.wip_limit(project_services.team_size(self.project))
        todo = list(WorkItem.objects.filter(project=self.project))
        for item in todo[:limit]:
            item.status = WorkItem.DOING
            item.save()
        with self.assertRaises(services.WipLimitReached):
            services.assign(todo[limit], self.members[2], START)
        # joining something already in progress is still fine
        services.assign(todo[0], self.members[2], START)

    def test_release_returns_an_unstaffed_item_to_todo(self):
        a1 = services.assign(self.items["T1"], self.members[0], START)
        a2 = services.assign(self.items["T1"], self.members[1], START)
        services.release(a1)
        self.items["T1"].refresh_from_db()
        self.assertEqual(self.items["T1"].status, WorkItem.DOING)
        services.release(a2)
        self.items["T1"].refresh_from_db()
        self.assertEqual(self.items["T1"].status, WorkItem.TODO)

    def test_load_by_member(self):
        services.assign(self.items["T1"], self.members[0], START)
        self.assertEqual(services.load_by_member(self.project), {m.name: int(m == self.members[0]) for m in self.members})


class EscalationTests(TestCase):
    def setUp(self):
        self.project = make_project()
        self.cal = project_services.calendar_for(self.project)
        self.item = make_items(self.project, {"T1": 3})["T1"]
        self.item.priority = 3
        self.item.save()
        self.member = self.project.members.first()
        services.assign(self.item, self.member, START)

    def test_not_due_the_day_before(self):
        after = rules.escalation_after_days(3)
        if after:
            self.assertEqual(services.due_for_escalation(self.project, self.cal.add(START, after - 1)), [])

    def test_due_after_the_period(self):
        after = rules.escalation_after_days(3)
        due = services.due_for_escalation(self.project, self.cal.add(START, after))
        self.assertEqual([a.item.code for a in due], ["T1"])

    def test_escalate_marks_and_does_not_repeat(self):
        today = self.cal.add(START, rules.escalation_after_days(3) + 1)
        self.assertEqual(len(services.escalate(self.project, today)), 1)
        self.assertEqual(Assignment.objects.get().escalated_on, today)
        self.assertEqual(services.escalate(self.project, today + dt.timedelta(days=1)), [])

    def test_released_assignments_are_not_escalated(self):
        services.release(Assignment.objects.get())
        self.assertEqual(services.due_for_escalation(self.project, dt.date(2025, 6, 2)), [])
