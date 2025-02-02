from django.urls import path

from .views import famous_tracks
from .views import home

app_name = "games"
urlpatterns = [
    path("", view=home, name="home"),
    path("famous_tracks/", view=famous_tracks, name="famous_tracks"),
]
