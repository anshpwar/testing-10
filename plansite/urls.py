from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("projects/", include("projects.urls")),
    path("milestones/", include("milestones.urls")),
    path("assignments/", include("assignments.urls")),
    path("timesheets/", include("timesheets.urls")),
    path("entries/", include("tasks.urls")),
]
