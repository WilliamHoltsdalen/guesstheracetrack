from django.urls import path

from .views import famous_tracks
from .views import home
from .views import start

app_name = "games"
urlpatterns = [
    path("", view=home, name="home"),
    path("famous_tracks/", view=famous_tracks, name="famous_tracks"),
    path("famous_tracks/start/", view=start, name="famous_tracks/start"),
]
