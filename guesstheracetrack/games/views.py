from random import choice

from django.shortcuts import render

from .models import RaceTrack


def home(request):
    return render(request, "games/home.html")


def famous_tracks(request):
    """Example view to test showing image from DB in template"""

    # Get random track from database
    pks = list(RaceTrack.objects.values_list("pk", flat=True))
    random_pk_1 = choice(pks)  # noqa: S311 (not for cryptographic purposes)
    pks.remove(random_pk_1)
    random_pk_2 = choice(pks)  # noqa: S311 (not for cryptographic purposes)
    pks.remove(random_pk_2)
    random_pk_3 = choice(pks)  # noqa: S311 (not for cryptographic purposes)

    correct_track = RaceTrack.objects.get(pk=random_pk_1)
    random_track_2 = RaceTrack.objects.get(pk=random_pk_2)
    random_track_3 = RaceTrack.objects.get(pk=random_pk_3)

    context = {
        "correct_track": correct_track,
        "track_2": random_track_2,
        "track_3": random_track_3,
    }

    return render(request, "games/famous_tracks.html", context)
