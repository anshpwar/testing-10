from django.contrib import admin

from .models import Dependency, Holiday, Member, Project, WorkItem


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "status", "start_on")


@admin.register(WorkItem)
class WorkItemAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "project", "duration_days", "status")
    list_filter = ("status", "project")


admin.site.register(Member)
admin.site.register(Holiday)
admin.site.register(Dependency)
