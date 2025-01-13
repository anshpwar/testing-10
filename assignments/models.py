from django.db import models


class Assignment(models.Model):
    ASSIGNED, RELEASED = "assigned", "released"
    STATES = [(ASSIGNED, "Assigned"), (RELEASED, "Released")]

    item = models.ForeignKey("projects.WorkItem", on_delete=models.CASCADE, related_name="assignments")
    member = models.ForeignKey("projects.Member", on_delete=models.CASCADE, related_name="assignments")
    assigned_on = models.DateField()
    hours_planned = models.PositiveIntegerField(default=8)
    state = models.CharField(max_length=8, choices=STATES, default=ASSIGNED)
    escalated_on = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["assigned_on", "id"]
