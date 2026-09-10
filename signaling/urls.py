from django.urls import path

from . import views

app_name = "signaling"

urlpatterns = [
    path("", views.index, name="index"),
]