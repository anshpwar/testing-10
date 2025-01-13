from django.contrib import admin

from .models import Milestone


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "due_on", "baseline_due_on")
