from django.urls import path

from . import views

urlpatterns = [
    path("<str:key>/", views.project_detail, name="project-detail"),
    path("<str:key>/schedule/", views.run_schedule, name="project-schedule"),
    path("<str:key>/critical/", views.critical_path, name="project-critical"),
    path("<str:key>/dependencies/", views.add_dependency, name="project-dependency"),
    path("<str:key>/sprints/", views.sprints, name="project-sprints"),
]
