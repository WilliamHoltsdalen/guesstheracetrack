import math
import time
import uuid
from random import sample
from random import shuffle

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth.decorators import login_required
from django.db.models import QuerySet
from django.shortcuts import redirect
from django.shortcuts import render

from guesstheracetrack.scores.models import Score

from .forms import TrackChoiceForm
from .models import GameSession
from .models import GameSessionTrack
from .models import RaceTrack
from .utils import SegmentImage

MIN_TRACKS_FOR_SESSION = 3


def home(request):
    context = {
        "messages": [
            "This site is still under development, so expect some bugs and "
            "glitches 🫣.",
        ],
    }
    return render(request, "games/home.html", context)


def get_active_game_session(user) -> GameSession | None:
    """Get the most recent incomplete game session for a user."""
    return (
        GameSession.objects.filter(user=user, is_completed=False)
        .order_by("-start_time")
        .first()
    )


def get_current_track(game_session) -> GameSessionTrack | None:
    """Get the current unanswered track for a game session."""
    return GameSessionTrack.objects.filter(
        session=game_session,
        score=0,
    ).first()


def get_game_session_track_objects(game_session) -> QuerySet[GameSessionTrack]:
    """Get all GameSessionTrack objects for a game session."""
    return GameSessionTrack.objects.filter(session=game_session)


def create_game_round(game_session, correct_track, pks, order):
    """Create a single game round with one correct and two incorrect tracks."""
    non_correct_pks = [pk for pk in pks if pk != correct_track.pk]
    incorrect_tracks = RaceTrack.objects.filter(
        pk__in=sample(non_correct_pks, k=2),
    )

    return GameSessionTrack.objects.create(
        session=game_session,
        correct_track=correct_track,
        incorrect_track_1=incorrect_tracks[0],
        incorrect_track_2=incorrect_tracks[1],
        order=order,
    )


@login_required
def start_session(request):
    pks = list(RaceTrack.objects.values_list("pk", flat=True))
    if len(pks) < MIN_TRACKS_FOR_SESSION:
        return redirect("games:home")

    game_session = GameSession.objects.create(user=request.user)

    # Select random tracks for the session
    num_rounds = min(10, len(pks) - 1)
    selected_tracks = list(
        RaceTrack.objects.filter(
            pk__in=sample(pks, k=num_rounds),
        ),
    )
    shuffle(selected_tracks)  # Randomize the order of tracks

    for i, track in enumerate(selected_tracks):
        create_game_round(game_session, track, pks, i)

    return redirect("games:famous_tracks")


@login_required
def famous_tracks(request):
    if request.method == "POST":
        return handle_track_submission(request)

    return handle_track_display(request)


def handle_track_display(request):
    """Handle GET request for track display."""
    game_session = get_active_game_session(request.user)

    if not game_session:
        return redirect("games:start_session")

    game_session_track = get_current_track(game_session)
    if not game_session_track:
        return redirect("games:start_session")

    track_list = [
        game_session_track.correct_track,
        game_session_track.incorrect_track_1,
        game_session_track.incorrect_track_2,
    ]
    shuffle(track_list)

    rounds = {
        i + 1: get_game_session_track_objects(game_session)
        .filter(order=i)
        .first()
        .score
        for i in range(game_session.tracks.count())
    }

    context = {
        "track_list": track_list,
        "correct_track_pk": game_session_track.correct_track.pk,
        "rounds": rounds,
        "current_round": game_session_track.order + 1,
        "number_of_rounds": game_session.tracks.count(),
    }

    return render(request, "games/famous_tracks.html", context)


def handle_track_submission(request):
    """Handle POST request for track submission."""
    form = TrackChoiceForm(request.POST)
    if not form.is_valid():
        return redirect("games:home")

    game_session = get_active_game_session(request.user)
    if not game_session:
        return redirect("games:home")

    game_session_track = get_current_track(game_session)
    track_pk = uuid.UUID(form.cleaned_data["track"])

    # Update score
    is_correct = game_session_track.correct_track.pk == track_pk
    game_session_track.score = 1 if is_correct else -1
    game_session_track.save()

    # Check if session is complete
    if game_session_track.order == game_session.tracks.count() - 1:
        return complete_session(request, game_session)

    return redirect("games:famous_tracks")


def complete_session(request, game_session):
    """Complete the game session and update scores."""
    total_score = get_game_session_track_objects(game_session).filter(score=1).count()
    game_session.score = total_score
    game_session.is_completed = True
    game_session.save()

    score, _ = Score.objects.get_or_create(user=request.user)
    score.score += total_score
    score.save()

    return redirect("games:session_complete")


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


@login_required
def restart_session(request):
    """Restart the game session, resetting all scores."""
    game_session = get_active_game_session(request.user)
    if game_session:
        game_session.delete()

    return redirect("games:start_session")


@login_required
def quit_session(request):
    """Quit the game session."""
    game_session = get_active_game_session(request.user)
    if game_session:
        game_session.delete()

    return redirect("games:home")


def get_segments(game_session):
    """Get the segments for the game session."""
    track_sessions = get_game_session_track_objects(game_session)

    image_path = track_sessions[1].correct_track.image.url
    segmenter = SegmentImage(image_path, 4)
    return segmenter()


@login_required
def competitive_mode(request):
    game_session = get_active_game_session(request.user)
    if not game_session:
        return redirect("games:start_session")
    segment_count = len(get_segments(game_session))
    count_root = range(int(math.sqrt(segment_count)))
    context = {
        "i": count_root,
        "j": count_root,
    }
    return render(request, "games/competitive_mode.html", context)


@login_required
def start_competitive_mode(request):
    game_session = get_active_game_session(request.user)
    segments = get_segments(game_session)
    segment_count = len(segments)

    shuffle(segments)

    channel_layer = get_channel_layer()
    for i in range(segment_count):
        async_to_sync(channel_layer.group_send)(
            "track_segments",
            {
                "type": "send_segments",
                "message": segments[i],
            },
        )
        time.sleep(1)

    return render(request, "games/competitive_mode.html")
