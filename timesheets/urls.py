from django.urls import path

from . import views

urlpatterns = [
    path("log/", views.log, name="timesheet-log"),
    path("<int:member_id>/week/<str:day>/", views.week, name="timesheet-week"),
]
