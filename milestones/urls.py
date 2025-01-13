from django.urls import path

from . import views

urlpatterns = [path("<int:pk>/status/", views.milestone_status, name="milestone-status")]
