from django.shortcuts import render

from .models import RaceTrack


def home(request):
    """Example view to test showing image from DB in template"""

    track = RaceTrack.objects.get(name="nurburgring")

    context = {
        "track": track,
    }

    return render(request, "games/track.html", context)