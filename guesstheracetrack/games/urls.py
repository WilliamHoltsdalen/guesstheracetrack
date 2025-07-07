from django.urls import path

from .views import competitive_mode
from .views import competitive_mode_quit_session
from .views import competitive_mode_restart_session
from .views import famous_tracks
from .views import famous_tracks_quit_session
from .views import famous_tracks_restart_session
from .views import home
from .views import session_complete
from .views import start_session

app_name = "games"
urlpatterns = [
    path("", view=home, name="home"),
    path("famous_tracks/", view=famous_tracks, name="famous_tracks"),
    path(
        "start_session/<str:game_type>/",
        view=start_session,
        name="start_session",
    ),
    path(
        "session_complete/<str:pk>/",
        view=session_complete,
        name="session_complete",
    ),
    path(
        "famous_tracks/restart_session/famous_tracks",
        view=famous_tracks_restart_session,
        name="restart_famous_tracks_session",
    ),
    path(
        "famous_tracks/restart_session/competitive_mode",
        view=competitive_mode_restart_session,
        name="restart_competitive_mode_session",
    ),
    path(
        "famous_tracks/quit_session/",
        view=famous_tracks_quit_session,
        name="famous_tracks_quit_session",
    ),
    path("competitive_mode/", view=competitive_mode, name="competitive_mode"),
    path(
        "competitive_mode/quit_session/",
        view=competitive_mode_quit_session,
        name="competitive_mode_quit_session",
    ),
]
