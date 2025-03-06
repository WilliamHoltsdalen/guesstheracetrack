from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from guesstheracetrack.games.models import GameSession

from .models import Score


def limited_leaderboard(request):
    scores = Score.objects.all().order_by("-score")[:5]

    leaderboard = populate_leaderboard_list(scores)

    context = {"leaderboard": leaderboard}
    return render(request, "scores/leaderboard.html", context)


@login_required
def full_leaderboard(request):
    scores = Score.objects.all().order_by("-score")

    leaderboard = populate_leaderboard_list(scores)
    context = {"leaderboard": leaderboard}
    return render(request, "scores/leaderboard.html", context)


def populate_leaderboard_list(scores) -> list:
    leaderboard = []
    for rank, score in enumerate(scores):
        leaderboard.append(
            {
                "name": score.user.name,
                "score": score.score,
                "rank": rank + 1,
                "games_played": GameSession.objects.filter(user=score.user).count(),
            },
        )
    return leaderboard
