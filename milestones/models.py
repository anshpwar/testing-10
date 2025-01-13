from django.db import models


class Milestone(models.Model):
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="milestones")
    name = models.CharField(max_length=80)
    due_on = models.DateField()
    baseline_due_on = models.DateField(null=True, blank=True)
    items = models.ManyToManyField("projects.WorkItem", blank=True, related_name="milestones")

    class Meta:
        ordering = ["due_on", "name"]

    def __str__(self):
        return self.name
