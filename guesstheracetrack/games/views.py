from random import choice

from django.shortcuts import render

from .models import RaceTrack


def home(request):
    """Example view to test showing image from DB in template"""

    # Get random track from database
    pks = RaceTrack.objects.values_list("pk", flat=True)
    random_pk = choice(pks)  # noqa: S311 (not for cryptographic purposes)
    random_track = RaceTrack.objects.get(pk=random_pk)

    context = {
        "track": random_track,
    }

    return render(request, "games/track.html", context)
