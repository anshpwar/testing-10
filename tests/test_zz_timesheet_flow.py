import datetime as dt
import json

from django.test import TestCase

from milestones.models import Milestone
from plankit import rules
from projects import services as project_services

from .factories import DIAMOND, START, make_items, make_project


class PlanToTimesheetFlowTests(TestCase):
    """Plan a small project, staff it, book time through the API and check the milestone forecast."""

    def setUp(self):
        self.project = make_project()
        self.items = make_items(self.project, *DIAMOND)
        self.member = self.project.members.get(seniority=3)

    def post(self, url, body):
        return self.client.post(url, json.dumps(body), content_type="application/json")

    def log(self, code, day, minutes):
        return self.post("/timesheets/log/", {"member": self.member.id, "item": code, "worked_on": day.isoformat(),
                                              "today": day.isoformat(), "minutes": minutes})

    def test_week_of_work(self):
        plan = self.post("/projects/ATLAS/schedule/", {}).json()
        self.assertEqual(plan["tasks"]["A"]["start"], "2025-01-13")
        body = {"project": "ATLAS", "item": "A", "member": self.member.id, "today": "2025-01-13"}
        self.assertEqual(self.post("/assignments/assign/", body).status_code, 201)
        per_day = rules.max_daily_hours(3) * 60
        for i in range(3):
            self.assertEqual(self.log("A", START + dt.timedelta(days=i), per_day).status_code, 201)
        resp = self.client.get(f"/timesheets/{self.member.id}/week/2025-01-15/")
        self.assertEqual(resp.json()["minutes"], 3 * per_day)
        self.assertEqual(resp.json()["week_start"], "2025-01-13")

    def test_day_full_and_weekend_errors(self):
        per_day = rules.max_daily_hours(3) * 60
        self.assertEqual(self.log("A", START, per_day).status_code, 201)
        resp = self.log("A", START, 1)
        self.assertEqual((resp.status_code, resp.json()["error"]), (422, "day_full"))
        self.assertEqual(self.log("A", dt.date(2025, 1, 18), 60).status_code, 400)

    def test_locked_entry_status(self):
        window = rules.timesheet_lock_days(3)
        cal = project_services.calendar_for(self.project)
        body = {"member": self.member.id, "item": "A", "worked_on": START.isoformat(),
                "today": cal.add(START, window + 1).isoformat(), "minutes": 60}
        resp = self.post("/timesheets/log/", body)
        self.assertEqual((resp.status_code, resp.json()["error"]), (423, "week_locked"))

    def test_bad_requests(self):
        self.assertEqual(self.post("/timesheets/log/", {"member": self.member.id}).status_code, 400)
        self.assertEqual(self.client.get("/timesheets/999/week/2025-01-13/").status_code, 404)
        self.assertEqual(self.client.get(f"/timesheets/{self.member.id}/week/yesterday/").status_code, 400)

    def test_milestone_forecast_after_scheduling(self):
        self.post("/projects/ATLAS/schedule/", {})
        milestone = Milestone.objects.create(project=self.project, name="Beta", due_on=dt.date(2025, 2, 3))
        milestone.items.set(self.items.values())
        data = self.client.get(f"/milestones/{milestone.id}/status/").json()
        self.assertEqual(data["forecast"], "2025-01-22")
        self.assertEqual(data["status"], "on_track")
        self.assertLess(data["slip_days"], 0)

    def test_unscheduled_milestone_is_a_conflict(self):
        milestone = Milestone.objects.create(project=self.project, name="Beta", due_on=dt.date(2025, 2, 3))
        self.assertEqual(self.client.get(f"/milestones/{milestone.id}/status/").status_code, 409)
        self.assertEqual(self.client.get("/milestones/999/status/").status_code, 404)
