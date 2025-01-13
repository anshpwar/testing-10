import datetime as dt
import json

from django.test import TestCase

from .factories import DIAMOND, make_items, make_project


class ProjectApiTests(TestCase):
    def setUp(self):
        self.project = make_project()
        self.items = make_items(self.project, *DIAMOND)

    def post(self, url, body):
        return self.client.post(url, json.dumps(body), content_type="application/json")

    def test_detail(self):
        data = self.client.get("/projects/ATLAS/").json()
        self.assertEqual(data, {"key": "ATLAS", "name": "ATLAS rollout", "status": "planning", "team_size": 3,
                                "counts": {"todo": 4, "doing": 0, "done": 0}})

    def test_unknown_project(self):
        self.assertEqual(self.client.get("/projects/NOPE/").status_code, 404)
        self.assertEqual(self.post("/projects/NOPE/schedule/", {}).status_code, 404)

    def test_schedule_endpoint(self):
        data = self.post("/projects/ATLAS/schedule/", {}).json()
        self.assertEqual(data["length_days"], 8)
        self.assertEqual(data["finish"], "2025-01-22")
        self.assertEqual(data["critical_path"], ["A", "C", "D"])
        self.assertEqual(data["tasks"]["B"], {"start": "2025-01-16", "finish": "2025-01-17", "slack": 2, "critical": False})
        self.assertGreaterEqual(data["committed_finish"], data["finish"])

    def test_critical_endpoint(self):
        data = self.client.get("/projects/ATLAS/critical/").json()
        self.assertEqual(data["critical_path"], ["A", "C", "D"])
        self.assertEqual(data["length_days"], 8)

    def test_dependency_endpoint(self):
        extra = make_items(self.project, {"E": 2})
        resp = self.post("/projects/ATLAS/dependencies/", {"item": "E", "depends_on": "D"})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(self.client.get("/projects/ATLAS/critical/").json()["critical_path"], ["A", "C", "D", "E"])
        self.assertEqual(extra["E"].needs.count(), 1)

    def test_dependency_loop_is_unprocessable(self):
        resp = self.post("/projects/ATLAS/dependencies/", {"item": "A", "depends_on": "D"})
        self.assertEqual(resp.status_code, 422)
        self.assertEqual(resp.json()["error"], "rejected")

    def test_dependency_bad_input(self):
        self.assertEqual(self.post("/projects/ATLAS/dependencies/", {"item": "A"}).status_code, 400)
        self.assertEqual(self.post("/projects/ATLAS/dependencies/", {"item": "A", "depends_on": "ZZ"}).status_code, 404)

    def test_sprints_endpoint(self):
        data = self.client.get("/projects/ATLAS/sprints/?count=2").json()
        self.assertEqual(len(data["sprints"]), 2)
        self.assertEqual(data["sprints"][0]["first"], dt.date(2025, 1, 13).isoformat())
        self.assertEqual(self.client.get("/projects/ATLAS/sprints/?count=x").status_code, 400)
