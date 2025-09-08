from django.urls import path
from . import views

app_name = "safety"
urlpatterns = [
    path("panel/", views.safety_panel, name="panel"),
]
