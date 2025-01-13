from django.db import models


class TimeEntry(models.Model):
    member = models.ForeignKey("projects.Member", on_delete=models.CASCADE, related_name="time_entries")
    item = models.ForeignKey("projects.WorkItem", on_delete=models.CASCADE, related_name="time_entries")
    worked_on = models.DateField()
    minutes = models.PositiveIntegerField()
    note = models.CharField(max_length=80, blank=True, default="")

    class Meta:
        ordering = ["worked_on", "id"]
