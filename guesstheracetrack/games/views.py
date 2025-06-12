import json
import math
from random import shuffle

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from .forms import TrackChoiceForm
from .models import GameSession
from .models import GameSessionTrack
from .services import competitive_mode_get_segments
from .services import get_active_game_session
from .services import get_current_game_session_track
from .services import get_game_session_track_objects
from .services import handle_competitive_mode_submission
from .services import handle_famous_tracks_submission
from .services import is_session_complete
from .services import start_new_game_session
from .tasks import cancel_send_segments_task
from .tasks import send_segments_task

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
# Common for all games
# ------------------------------------------------------------------------------


@login_required
def start_session(request: HttpRequest, game_type: str) -> HttpResponse:
    """Start a new game session for a user of the specified game type."""
    assert game_type is not None
    user = request.user
    start_new_game_session(user, game_type)

    match game_type:
        case "famous_tracks":
            return redirect("games:famous_tracks")
        case "competitive_mode":
            return redirect("games:competitive_mode")
        case _:
            return redirect("games:home")


# ------------------------------------------------------------------------------
# Views for famous tracks game
# ------------------------------------------------------------------------------


@login_required
def famous_tracks(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        return famous_tracks_handle_track_submission(request)

    context = famous_tracks_display_context(request)
    if not context:
        return redirect("games:start_session", game_type="famous_tracks")

    return render(request, "games/famous_tracks.html", context)


@login_required
def session_complete(request, game_type: str) -> HttpResponse:
    """This view is called when a round is complete. It will show a complete
    round overview with results."""

    # Get the game session
    game_session = (
        GameSession.objects.filter(
            user=request.user,
            is_completed=True,
            game_type=game_type,
        )
        .order_by("-start_time")
        .first()
    )
    if not game_session:
        return redirect("games:home")

    rounds = {}
    total_score = 0
    for track_round in range(game_session.tracks.count()):
        game_session_track = GameSessionTrack.objects.filter(
            session=game_session,
            order=track_round,
        ).first()
        assert game_session_track
        if not game_session_track.submitted_track:
            submitted_track = "(An error occurred)"
        else:
            submitted_track = game_session_track.submitted_track.name

        rounds[track_round + 1] = {
            "track_name": game_session_track.correct_track.name,
            "submitted_track": submitted_track,
            "score": GameSessionTrack.objects.filter(
                session=game_session,
                order=track_round,
            )
            .first()
            .score,
        }
        score = rounds[track_round + 1]["score"]
        total_score += score if score > 0 else 0

    game_type = game_session.game_type
    context = {
        "rounds": rounds,
        "total_score": total_score,
        "game_type": game_type,
    }

    return render(request, "games/session_complete.html", context)


@login_required
def famous_tracks_restart_session(request) -> HttpResponse:
    """Restart the famous tracks game session, resetting all scores."""
    game_session = get_active_game_session(request.user, "famous_tracks")
    if game_session:
        game_session.delete()

    return redirect("games:start_session", game_type="famous_tracks")


@login_required
def famous_tracks_quit_session(request) -> HttpResponse:
    """Quit the famous tracks game session."""
    game_session = get_active_game_session(request.user, "famous_tracks")
    if game_session:
        game_session.delete()

    return redirect("games:home")


def famous_tracks_display_context(request) -> dict:
    """Handle context for famous tracks game track display."""
    game_session = get_active_game_session(request.user, "famous_tracks")
    game_session_track = get_current_game_session_track(game_session)

    if game_session is None or game_session_track is None:
        return {}

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
        "game_restart_url": reverse("games:restart_famous_tracks_session"),
        "game_quit_url": reverse("games:famous_tracks_quit_session"),
    }


@login_required
def famous_tracks_handle_track_submission(request) -> HttpResponse:
    """Handle POST request for track submission in famous tracks game."""
    form = TrackChoiceForm(request.POST)
    assert form.is_valid()

    handle_famous_tracks_submission(request.user, form)
    if is_session_complete(request.user, "famous_tracks"):
        return redirect("games:session_complete", game_type="famous_tracks")
    return redirect("games:famous_tracks")


# ------------------------------------------------------------------------------
# Views for competitive mode game, and related functions
# ------------------------------------------------------------------------------


@login_required
def competitive_mode(request) -> HttpResponse:
    if request.method == "POST":
        return competitive_mode_handle_post(request)

    context = competitive_mode_display_context(request)
    if not isinstance(context, dict):
        return context

    return render(request, "games/competitive_mode.html", context)


@login_required
def competitive_mode_restart_session(request) -> HttpResponse:
    """Restart the competitive mode session."""
    game_session = get_active_game_session(request.user, "competitive_mode")
    if game_session:
        game_session.delete()
    return redirect("games:start_session", game_type="competitive_mode")


@login_required
def competitive_mode_quit_session(request) -> HttpResponse:
    """Quit the competitive mode game session."""
    game_session = get_active_game_session(request.user, "competitive_mode")
    if game_session:
        game_session.delete()

    return redirect("games:home")


def competitive_mode_handle_post(request) -> HttpResponse:
    """Handle POST request for competitive mode."""
    try:
        body_unicode = request.body.decode("utf-8")
        body = json.loads(body_unicode)
        if body["message"] == "start_sending_segments":
            competitive_mode_send_segments(request)
            return redirect("games:competitive_mode")
    except json.JSONDecodeError:
        # This is a form submission, not a JSON request
        return competitive_mode_handle_track_submission(request)
    except Exception:  # noqa: BLE001 This is a blind exception for now
        # Cancel tasks for this specific session
        game_session = get_active_game_session(request.user, "competitive_mode")
        if game_session:
            cancel_send_segments_task(game_session.id)
        # Return error response for JSON requests
        return HttpResponse("Error processing request", status=500)

    return redirect("games:competitive_mode")


def competitive_mode_handle_track_submission(request):
    """Handle POST request for track submission in competitive mode."""
    form = TrackChoiceForm(request.POST)
    assert form.is_valid()

    handle_competitive_mode_submission(request.user, form)

    if is_session_complete(request.user, "competitive_mode"):
        return redirect("games:session_complete", game_type="competitive_mode")

    return redirect("games:competitive_mode")


def competitive_mode_display_context(request):
    """Handle context for competitive mode."""
    game_session = get_active_game_session(request.user, "competitive_mode")
    game_session_track = get_current_game_session_track(game_session)

    if game_session is None or game_session_track is None:
        return redirect("games:start_session", game_type="competitive_mode")

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
    count_root = range(int(math.sqrt(len(segments))))

    return {
        "track_list": track_list,
        "correct_track_pk": game_session_track.correct_track.pk,
        "rounds": rounds,
        "current_round": game_session_track.order + 1,
        "number_of_rounds": game_session.tracks.count(),
        "i": count_root,
        "j": count_root,
        "game_restart_url": reverse("games:restart_competitive_mode_session"),
        "game_quit_url": reverse("games:competitive_mode_quit_session"),
    }


def competitive_mode_send_segments(request):
    game_session = get_active_game_session(request.user, "competitive_mode")
    game_session_track = get_current_game_session_track(game_session)

    # Cancel any existing task for this session before starting a new one
    cancel_send_segments_task(game_session.id)

    segments = competitive_mode_get_segments(request)
    shuffle(segments)

    # Session-specific group name
    group_name = f"track_segments_{game_session.id}"
    send_segments_task.delay(segments, group_name)  # type: ignore[misc]
    game_session_track.revealed_at = timezone.localtime()
    game_session_track.save()
