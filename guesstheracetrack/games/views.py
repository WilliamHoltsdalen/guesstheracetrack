import uuid
from random import choice
from random import shuffle

from django.shortcuts import redirect
from django.shortcuts import render

from .forms import TrackChoiceForm
from .models import GameSession
from .models import GameSessionTrack
from .models import RaceTrack

MIN_TRACKS_FOR_SESSION = 3


def home(request):
    return render(request, "games/home.html")


def start_session(request):
    # Minimum of 3 tracks required

    pks = list(RaceTrack.objects.values_list("pk", flat=True)).copy()
    unused_pks = pks.copy()
    # If there are less than minimum of 3 tracks in the database, redirect
    if len(pks) < MIN_TRACKS_FOR_SESSION:
        return redirect("games:home")

    # Create a new game session with rounds
    game_session = GameSession.objects.create(
        user=request.user,
    )

    # Get (max 10) random tracks from database, ensuring no duplicates
    for i in range(min(10, len(pks) - 1)):
        correct_track_pk = choice(unused_pks)  # noqa: S311 (not for cryptographic purposes)
        unused_pks.remove(correct_track_pk)
        non_correct_pks = pks.copy()
        non_correct_pks.remove(correct_track_pk)

        incorrect_track_1_pk = choice(non_correct_pks)  # noqa: S311 (not for cryptographic purposes)
        non_correct_pks.remove(incorrect_track_1_pk)
        incorrect_track_2_pk = choice(non_correct_pks)  # noqa: S311 (not for cryptographic purposes)

        correct_track = RaceTrack.objects.get(pk=correct_track_pk)
        incorrect_track_1 = RaceTrack.objects.get(pk=incorrect_track_1_pk)
        incorrect_track_2 = RaceTrack.objects.get(pk=incorrect_track_2_pk)

        GameSessionTrack.objects.create(
            session=game_session,
            correct_track=correct_track,
            incorrect_track_1=incorrect_track_1,
            incorrect_track_2=incorrect_track_2,
            order=i,
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
            .order_by("-start_time")
            .first()
        )
        game_session_track = GameSessionTrack.objects.filter(
            session=game_session,
            score=0,
        ).first()

        if game_session_track.correct_track.pk == track_pk:
            game_session_track.score += 1
            game_session_track.save()
        else:
            game_session_track.score = -1
            game_session_track.save()

        if game_session_track.order == game_session.tracks.count() - 1:
            game_session.is_completed = True
            game_session.save()
            return redirect("games:session_complete")

        return redirect("games:famous_tracks")

    # Load the page
    # Check if the user is trying to resume an old game session
    game_session = (
        GameSession.objects.filter(user=request.user).order_by("-start_time").first()
    )
    if game_session is None or game_session.is_completed is True:
        return redirect("games:start_session")

    # Get correct track from database
    game_session = (
        GameSession.objects.filter(user=request.user, is_completed=False)
        .order_by("-start_time")
        .first()
    )
    game_session_track = GameSessionTrack.objects.filter(
        session=game_session,
        score=0,
    ).first()

    # Get the track choices for the current round and shuffle them
    track_list = [
        game_session_track.correct_track,
        game_session_track.incorrect_track_1,
        game_session_track.incorrect_track_2,
    ]
    shuffle(track_list)

    # Get status of game session
    rounds = {}
    number_of_rounds = game_session.tracks.count()
    for track_round in range(number_of_rounds):
        rounds[track_round + 1] = (
            GameSessionTrack.objects.filter(
                session=game_session,
                order=track_round,
            )
            .first()
            .score
        )

    # Get round number for the current round
    current_round = game_session_track.order + 1

    context = {
        "track_list": track_list,
        "correct_track_pk": game_session_track.correct_track.pk,
        "rounds": rounds,
        "current_round": current_round,
        "number_of_rounds": number_of_rounds,
    }

    return render(request, "games/famous_tracks.html", context)


def session_complete(request):
    """This view is called when a round is complete. It will show a complete
    round overview with results."""

    # Get the game session
    game_session = (
        GameSession.objects.filter(user=request.user, is_completed=True)
        .order_by("-start_time")
        .first()
    )
    if not game_session:
        return redirect("games:home")

    rounds = {}
    total_score = 0
    for track_round in range(game_session.tracks.count()):
        rounds[track_round + 1] = {
            "track_name": GameSessionTrack.objects.filter(
                session=game_session,
                order=track_round,
            )
            .first()
            .correct_track.name,
            "score": GameSessionTrack.objects.filter(
                session=game_session,
                order=track_round,
            )
            .first()
            .score,
        }
        if rounds[track_round + 1]["score"] == 1:
            total_score += 1

    context = {
        "rounds": rounds,
        "total_score": total_score,
    }

    return render(request, "games/session_complete.html", context)
