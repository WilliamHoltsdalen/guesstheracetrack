from django.urls import path

from .views import full_leaderboard

app_name = "scores"
urlpatterns = [
    path("leaderboard/", view=full_leaderboard, name="leaderboard"),
]
