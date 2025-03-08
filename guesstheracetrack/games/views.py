import json
import math
import time
import uuid
from random import sample
from random import shuffle

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.contrib.auth.decorators import login_required
from django.db.models import QuerySet
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone

from config.celery_app import app as celery_app
from guesstheracetrack.scores.models import Score

from .forms import TrackChoiceForm
from .models import GameSession
from .models import GameSessionTrack
from .models import RaceTrack
from .utils import SegmentImage

MIN_TRACKS_FOR_SESSION = 3

# ------------------------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------------------------


def get_current_game_session_track(game_session) -> GameSessionTrack | None:
    """Get the current unanswered game session track for a game session."""
    return GameSessionTrack.objects.filter(
        session=game_session,
        score=0,
    ).first()


def get_active_game_session(user, game_type):
    """Get the most recent incomplete game session for a user."""
    return (
        GameSession.objects.filter(user=user, is_completed=False, game_type=game_type)
        .order_by("-start_time")
        .first()
    )


def get_game_session_track_objects(game_session) -> QuerySet[GameSessionTrack]:
    """Get all GameSessionTrack objects for a game session."""
    return GameSessionTrack.objects.filter(session=game_session)


def start_session(user, game_type) -> None:
    """Start a new game session for a user of the specified game type."""
    pks = list(RaceTrack.objects.values_list("pk", flat=True))
    if len(pks) < MIN_TRACKS_FOR_SESSION:
        return redirect("games:home")

    game_session = GameSession.objects.create(user=user, game_type=game_type)

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
    return None


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


def complete_session(request, game_type):
    """Complete the game session and update the total score."""
    game_session = get_active_game_session(request.user, game_type)
    game_session_track_objects = get_game_session_track_objects(game_session)
    total_score = 0
    for game_session_track in game_session_track_objects:
        total_score += game_session_track.score if game_session_track.score > 0 else 0

    game_session.score = total_score
    game_session.is_completed = True
    game_session.save()

    score, _ = Score.objects.get_or_create(user=request.user)
    score.score += total_score
    score.save()
    return redirect("games:session_complete")


# ------------------------------------------------------------------------------
# Views for home page
# ------------------------------------------------------------------------------
def home(request):
    context = {
        "messages": [
            "This site is still under development, so expect some bugs and "
            "glitches 🫣.",
        ],
    }
    return render(request, "games/home.html", context)


# ------------------------------------------------------------------------------
# Views for famous tracks game and related functions
# ------------------------------------------------------------------------------


@login_required
def famous_tracks(request):
    if request.method == "POST":
        return famous_tracks_handle_track_submission(request)

    context = famous_tracks_display_context(request)
    if not isinstance(context, dict):
        return context

    return render(request, "games/famous_tracks.html", context)


@login_required
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
        score = rounds[track_round + 1]["score"]
        total_score += score if score > 0 else 0

    context = {
        "rounds": rounds,
        "total_score": total_score,
    }

    return render(request, "games/session_complete.html", context)


@login_required
def famous_tracks_restart_session(request):
    """Restart the famous tracks game session, resetting all scores."""
    game_session = get_active_game_session(request.user, "famous_tracks")
    if game_session:
        game_session.delete()

    return redirect("games:start_session")


@login_required
def famous_tracks_quit_session(request):
    """Quit the famous tracks game session."""
    game_session = get_active_game_session(request.user, "famous_tracks")
    if game_session:
        game_session.delete()

    return redirect("games:home")


def famous_tracks_display_context(request):
    """Handle context for famous tracks game track display."""
    game_session = get_active_game_session(request.user, "famous_tracks")
    game_session_track = get_current_game_session_track(game_session)

    if game_session is None or game_session_track is None:
        start_session(request.user, "famous_tracks")
        return redirect("games:famous_tracks")

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

    return {
        "track_list": track_list,
        "correct_track_pk": game_session_track.correct_track.pk,
        "rounds": rounds,
        "current_round": game_session_track.order + 1,
        "number_of_rounds": game_session.tracks.count(),
    }


def famous_tracks_handle_track_submission(request):
    """Handle POST request for track submission in famous tracks game."""
    form = TrackChoiceForm(request.POST)
    if not form.is_valid():
        return None

    game_session = get_active_game_session(request.user, "famous_tracks")
    if not game_session:
        return None

    game_session_track = get_current_game_session_track(game_session)
    track_pk = uuid.UUID(form.cleaned_data["track"])

    # Update score
    is_correct = game_session_track.correct_track.pk == track_pk
    game_session_track.score = 1 if is_correct else -1
    game_session_track.save()

    # Check if session is complete
    if game_session_track.order == game_session.tracks.count() - 1:
        return complete_session(request, "famous_tracks")
    return redirect("games:famous_tracks")


# ------------------------------------------------------------------------------
# Views for competitive mode game, and related functions
# ------------------------------------------------------------------------------


@login_required
def competitive_mode(request):
    if request.method == "POST":
        return competitive_mode_handle_post(request)

    context = competitive_mode_display_context(request)
    if not isinstance(context, dict):
        return context

    return render(request, "games/competitive_mode.html", context)


def competitive_mode_handle_post(request):
    """Handle POST request for competitive mode."""
    try:
        body_unicode = request.body.decode("utf-8")
        body = json.loads(body_unicode)
        if body["message"] == "start_sending_segments":
            competitive_mode_send_segments(request)
            return redirect("games:competitive_mode")
    except Exception:  # noqa: BLE001 This is a blind exception for now
        cancel_send_segments_task()
        return competitive_mode_handle_track_submission(request)


def competitive_mode_handle_track_submission(request):
    """Handle POST request for track submission in competitive mode."""
    form = TrackChoiceForm(request.POST)
    if not form.is_valid():
        return None

    game_session = get_active_game_session(request.user, "competitive_mode")
    game_session_track = get_current_game_session_track(game_session)
    track_pk = uuid.UUID(form.cleaned_data["track"])

    # If the track has not been revealed yet, redirect to the game page
    if not game_session_track.revealed_at:
        return redirect("games:competitive_mode")

    # Update track submission time
    game_session_track.submitted_at = timezone.localtime()

    # Update score
    is_correct = game_session_track.correct_track.pk == track_pk
    if not is_correct:
        game_session_track.score = -1
    else:
        revealed_at = game_session_track.revealed_at
        submitted_at = game_session_track.submitted_at

        if revealed_at and submitted_at:
            time_difference = submitted_at - revealed_at
            if time_difference.total_seconds() < 10:  # noqa: PLR2004 This is a magic number for now
                game_session_track.score = 10 - time_difference.total_seconds()
            else:
                game_session_track.score = 1

    game_session_track.save()

    # Check if session is complete
    if game_session_track.order == game_session.tracks.count() - 1:
        return complete_session(request, "competitive_mode")

    return redirect("games:competitive_mode")


def competitive_mode_get_segments(request):
    """Get the segments for the game session."""
    game_session = get_active_game_session(request.user, "competitive_mode")
    game_session_track = get_current_game_session_track(game_session)

    image_path = game_session_track.correct_track.image.url
    segmenter = SegmentImage(image_path, 4)
    return segmenter()


def competitive_mode_display_context(request):
    """Handle context for competitive mode."""
    game_session = get_active_game_session(request.user, "competitive_mode")
    game_session_track = get_current_game_session_track(game_session)
    if game_session is None or game_session_track is None:
        start_session(request.user, "competitive_mode")
        return redirect("games:competitive_mode")

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

    segments = competitive_mode_get_segments(request)
    segment_count = len(segments)
    count_root = range(int(math.sqrt(segment_count)))

    return {
        "track_list": track_list,
        "correct_track_pk": game_session_track.correct_track.pk,
        "rounds": rounds,
        "current_round": game_session_track.order + 1,
        "number_of_rounds": game_session.tracks.count(),
        "i": count_root,
        "j": count_root,
    }


def competitive_mode_send_segments(request):
    game_session = get_active_game_session(request.user, "competitive_mode")
    game_session_track = get_current_game_session_track(game_session)

    segments = competitive_mode_get_segments(request)
    shuffle(segments)

    send_segments_task.delay(segments, "track_segments")
    game_session_track.revealed_at = timezone.localtime()
    game_session_track.save()


@shared_task(name="games.tasks.send_segments_task")
def send_segments_task(segments, room_name):
    channel_layer = get_channel_layer()
    for segment in segments:
        async_to_sync(channel_layer.group_send)(
            room_name,
            {
                "type": "send_segments",
                "message": segment,
            },
        )
        time.sleep(1)


def cancel_send_segments_task():
    """Cancel the send segments task."""
    inspector = celery_app.control.inspect()
    active_tasks = inspector.active()
    if active_tasks:
        for tasks in active_tasks.values():
            for task in tasks:
                if task["name"] == "games.tasks.send_segments_task":
                    celery_app.control.revoke(task["id"], terminate=True)
