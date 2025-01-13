import json

from django.test import TestCase

from plankit import rules
from projects.models import WorkItem

from .factories import make_items, make_project


class AssignmentApiTests(TestCase):
    def setUp(self):
        self.project = make_project()
        self.items = make_items(self.project, {f"T{i}": 2 for i in range(1, 7)})
        self.member = self.project.members.get(seniority=1)

    def assign(self, code, member=None, today="2025-01-13"):
        body = {"project": "ATLAS", "item": code, "member": (member or self.member).id, "today": today}
        return self.client.post("/assignments/assign/", json.dumps(body), content_type="application/json")

    def test_assign_starts_the_item(self):
        resp = self.assign("T1")
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.json()["item_status"], "doing")

    def test_bad_requests(self):
        self.assertEqual(self.client.post("/assignments/assign/", "{", content_type="application/json").status_code, 400)
        self.assertEqual(self.assign("ZZ").status_code, 404)
        self.assertEqual(self.assign("T1", today="soon").status_code, 400)

    def test_person_cap_is_reported(self):
        WorkItem.objects.filter(project=self.project).update(status=WorkItem.DOING)
        cap = rules.max_assignments_per_person(self.member.seniority)
        for i in range(1, cap + 1):
            self.assertEqual(self.assign(f"T{i}").status_code, 201)
        resp = self.assign(f"T{cap + 1}")
        self.assertEqual((resp.status_code, resp.json()["error"]), (422, "person_overloaded"))

    def test_wip_limit_is_reported(self):
        limit = rules.wip_limit(3)
        others = list(self.project.members.exclude(pk=self.member.pk))
        codes = list(self.items)
        for i in range(limit):
            self.assertEqual(self.assign(codes[i], others[i % 2]).status_code, 201)
        resp = self.assign(codes[limit], others[0])
        self.assertEqual((resp.status_code, resp.json()["error"]), (422, "wip_limit"))

    def test_escalation_listing(self):
        self.assign("T1")
        far = self.client.get("/assignments/ATLAS/escalations/?today=2025-06-02").json()
        self.assertEqual(far["due"], [{"item": "T1", "member": self.member.name, "priority": 2}])
        early = self.client.get("/assignments/ATLAS/escalations/?today=2025-01-13").json()
        self.assertEqual(early["due"] == [], rules.escalation_after_days(2) > 0)
        self.assertEqual(self.client.get("/assignments/ATLAS/escalations/").status_code, 400)
        self.assertEqual(self.client.get("/assignments/NOPE/escalations/?today=2025-01-13").status_code, 404)
