from django.contrib import admin

from .models import Assignment


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("item", "member", "assigned_on", "state")
    list_filter = ("state",)
