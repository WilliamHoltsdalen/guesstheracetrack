import uuid
from random import choice
from random import shuffle

from django.shortcuts import redirect
from django.shortcuts import render

from .forms import TrackChoiceForm
from .models import GameSession
from .models import GameSessionTrack
from .models import RaceTrack


def home(request):
    return render(request, "games/home.html")


def start(request):
    # Get 3 random track from database
    pks = list(RaceTrack.objects.values_list("pk", flat=True))
    random_pk_1 = choice(pks)  # noqa: S311 (not for cryptographic purposes)
    pks.remove(random_pk_1)
    random_pk_2 = choice(pks)  # noqa: S311 (not for cryptographic purposes)
    pks.remove(random_pk_2)
    random_pk_3 = choice(pks)  # noqa: S311 (not for cryptographic purposes)

    # Get race tracks from database
    correct_track = RaceTrack.objects.get(pk=random_pk_1)
    random_track_2 = RaceTrack.objects.get(pk=random_pk_2)
    random_track_3 = RaceTrack.objects.get(pk=random_pk_3)

    track_list = [correct_track, random_track_2, random_track_3]
    shuffle(track_list)

    # Create a new game session
    game_session = GameSession.objects.create(
        user=request.user,
    )
    game_session_track_list = []

    for i, track in enumerate(track_list):
        game_session_track_list.append(
            GameSessionTrack.objects.create(
                session=game_session,
                track=track,
                order=i,
            ),
        )
    return redirect("games:famous_tracks")


def famous_tracks(request):
    # If the user submits a track choice...
    if request.method == "POST":
        form = TrackChoiceForm(request.POST)
        if not form.is_valid():
            return redirect("games:home")
        track_pk = uuid.UUID(form.cleaned_data["track"])

        game_session = (
            GameSession.objects.filter(user=request.user, is_completed=False)
            .order_by("start_time")
            .first()
        )
        game_session_track = GameSessionTrack.objects.filter(
            session=game_session,
            score=0,
        ).first()

        if game_session_track.track.pk == track_pk:
            game_session_track.score += 1
            game_session_track.save()
        else:
            game_session_track.score = -1
            game_session_track.save()

        return redirect("games:famous_tracks")

    # Load the page
    # Get correct track from database
    game_session = (
        GameSession.objects.filter(user=request.user, is_completed=False)
        .order_by("start_time")
        .first()
    )
    if game_session is None:
        return redirect("games:home")
    game_session_track = GameSessionTrack.objects.filter(
        session=game_session,
        score=0,
    ).first()
    if game_session_track is None:
        return redirect("games:home")

    # Remove the correct track from the list of tracks, and get 2 random ones
    pks = list(RaceTrack.objects.values_list("pk", flat=True))
    pks.remove(game_session_track.track.pk)
    random_pk_2 = choice(pks)  # noqa: S311 (not for cryptographic purposes)
    pks.remove(random_pk_2)
    random_pk_3 = choice(pks)  # noqa: S311 (not for cryptographic purposes)

    correct_track = game_session_track.track
    random_track_2 = RaceTrack.objects.get(pk=random_pk_2)
    random_track_3 = RaceTrack.objects.get(pk=random_pk_3)

    track_list = [correct_track, random_track_2, random_track_3]
    shuffle(track_list)

    context = {
        "track_list": track_list,
        "correct_track_pk": correct_track.pk,
    }

    return render(request, "games/famous_tracks.html", context)
