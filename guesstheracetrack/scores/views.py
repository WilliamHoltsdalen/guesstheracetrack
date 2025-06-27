from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
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

    paginator = Paginator(scores, 10)  # Show 10 scores per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    leaderboard = populate_leaderboard_list(page_obj.object_list, page_obj)

    context = {
        "leaderboard": leaderboard,
        "page_obj": page_obj,
    }
    return render(request, "scores/leaderboard.html", context)


def populate_leaderboard_list(scores, page_obj=None) -> list:
    leaderboard = []
    # Calculate the starting rank based on the current page
    start_rank = 1
    if page_obj and page_obj.number > 1:
        start_rank = (page_obj.number - 1) * page_obj.paginator.per_page + 1

    for rank, score in enumerate(scores):
        leaderboard.append(
            {
                "name": score.user.name,
                "score": score.score,
                "rank": start_rank + rank,
                "games_played": GameSession.objects.filter(user=score.user).count(),
            },
        )
    return leaderboard
