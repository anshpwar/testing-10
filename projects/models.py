from django.db import models


class Project(models.Model):
    PLANNING, ACTIVE, DONE = "planning", "active", "done"
    STATUSES = [(PLANNING, "Planning"), (ACTIVE, "Active"), (DONE, "Done")]

    key = models.CharField(max_length=12, unique=True)
    name = models.CharField(max_length=80)
    start_on = models.DateField()
    status = models.CharField(max_length=8, choices=STATUSES, default=PLANNING)
    workweek = models.PositiveSmallIntegerField(default=31)

    def __str__(self):
        return self.key


class Member(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="members")
    name = models.CharField(max_length=80)
    seniority = models.PositiveSmallIntegerField(default=1)
    hourly_rate_cents = models.PositiveIntegerField(default=5000)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Holiday(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="holidays")
    on = models.DateField()
    label = models.CharField(max_length=40, blank=True, default="")

    class Meta:
        unique_together = [("project", "on")]
        ordering = ["on"]


class WorkItem(models.Model):
    TODO, DOING, DONE = "todo", "doing", "done"
    STATUSES = [(TODO, "To do"), (DOING, "In progress"), (DONE, "Done")]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="items")
    code = models.CharField(max_length=16)
    title = models.CharField(max_length=120)
    duration_days = models.PositiveIntegerField(default=1)
    priority = models.PositiveSmallIntegerField(default=2)
    status = models.CharField(max_length=8, choices=STATUSES, default=TODO)
    not_before = models.DateField(null=True, blank=True)
    planned_start = models.DateField(null=True, blank=True)
    planned_finish = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = [("project", "code")]
        ordering = ["code"]

    def __str__(self):
        return f"{self.project.key}-{self.code}"


class Dependency(models.Model):
    item = models.ForeignKey(WorkItem, on_delete=models.CASCADE, related_name="needs")
    depends_on = models.ForeignKey(WorkItem, on_delete=models.CASCADE, related_name="blocks")

    class Meta:
        unique_together = [("item", "depends_on")]
