from django.urls import path

from . import views

urlpatterns = [
    path("assign/", views.assign, name="assignment-assign"),
    path("<str:key>/escalations/", views.escalations, name="assignment-escalations"),
]
