from django.urls import path
from . import views

app_name = "core"
urlpatterns = [
    path("", views.home, name="home"),
    path("pulse/", views.pulse, name="pulse"),
    path("spots.json", views.spots_geojson, name="spots_geojson"),
]