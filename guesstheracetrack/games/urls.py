from django.urls import path

from .views import famous_tracks
from .views import home
from .views import quit_session
from .views import restart_session
from .views import session_complete
from .views import start_session

app_name = "games"
urlpatterns = [
    path("", view=home, name="home"),
    path("famous_tracks/", view=famous_tracks, name="famous_tracks"),
    path(
        "famous_tracks/start_session/",
        view=start_session,
        name="start_session",
    ),
    path(
        "famous_tracks/session_complete/",
        view=session_complete,
        name="session_complete",
    ),
    path(
        "famous_tracks/restart_session/",
        view=restart_session,
        name="restart_session",
    ),
    path("famous_tracks/quit_session/", view=quit_session, name="quit_session"),
]
