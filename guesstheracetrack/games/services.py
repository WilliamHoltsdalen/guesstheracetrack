import uuid
from random import sample
from random import shuffle

from django.utils import timezone

from guesstheracetrack.scores.models import Score

from .models import GameSession
from .models import GameSessionTrack
from .models import RaceTrack
from .utils import SegmentImage

MIN_TRACKS_FOR_SESSION = 3
MAX_COMP_ROUND_TIME = 10


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


def get_game_session_track_objects(game_session):
    """Get all GameSessionTrack objects for a game session."""
    return GameSessionTrack.objects.filter(session=game_session)


def start_new_game_session(user, game_type: str):
    # End any existing active session for this game_type
    if not user:
        errormsg = "User is not set"
        raise ValueError(errormsg)
    if not game_type:
        errormsg = "Game type is not set"
        raise ValueError(errormsg)

    existing_session = get_active_game_session(user, game_type)
    if existing_session:
        existing_session.delete()

    pks = list(RaceTrack.objects.values_list("pk", flat=True))
    if len(pks) < MIN_TRACKS_FOR_SESSION:
        errormsg = "Not enough tracks to start a session"
        raise ValueError(errormsg)

    game_session = GameSession.objects.create(user=user, game_type=game_type)
    if not game_session.pk:
        errormsg = "Game session not created"
        raise ValueError(errormsg)

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


def create_game_round(game_session, correct_track, pks, order):
    """Create a single game round with one correct and two incorrect tracks."""
    non_correct_pks = [pk for pk in pks if pk != correct_track.pk]
    incorrect_tracks = sample(non_correct_pks, k=2)

    # NOTE: Fetching the tracks here to avoid problems with the queryset
    incorrect_tracks = list(RaceTrack.objects.filter(pk__in=incorrect_tracks))

    if len(incorrect_tracks) != 2:  # noqa: PLR2004
        errormsg = "Incorrect track count is not 2"
        raise ValueError(errormsg)
    if incorrect_tracks[0].pk == incorrect_tracks[1].pk:
        errormsg = "Incorrect tracks are the same"
        raise ValueError(errormsg)

    return GameSessionTrack.objects.create(
        session=game_session,
        correct_track=correct_track,
        incorrect_track_1=incorrect_tracks[0],
        incorrect_track_2=incorrect_tracks[1],
        order=order,
    )


def complete_session(user, game_type):
    """Complete the game session and update the total score."""
    game_session = get_active_game_session(user, game_type)
    game_session_track_objects = get_game_session_track_objects(game_session)
    total_score = 0
    for game_session_track in game_session_track_objects:
        total_score += game_session_track.score if game_session_track.score > 0 else 0

    game_session.score = total_score
    game_session.is_completed = True
    game_session.end_time = timezone.now()
    game_session.save()

    score, _ = Score.objects.get_or_create(user=user)
    score.score += total_score
    score.save()


def is_session_complete(user, game_type) -> bool:
    """Check if a game session is complete."""
    game_session = (
        GameSession.objects.filter(user=user, game_type=game_type)
        .order_by("-start_time")
        .first()
    )
    return game_session.is_completed


def handle_famous_tracks_submission(user, form) -> None:
    """Handle track submission for a game sessio, of the famous tracks game."""
    game_session = get_active_game_session(user, "famous_tracks")
    if not game_session:
        errormsg = "No active game session"
        raise ValueError(errormsg)

    game_session_track = get_current_game_session_track(game_session)
    track_pk = uuid.UUID(form.cleaned_data["track"])

    # Update submitted track
    game_session_track.submitted_at = timezone.now()
    game_session_track.submitted_track = RaceTrack.objects.get(pk=track_pk)
    game_session_track.save()

    # Update score
    is_correct = game_session_track.correct_track.pk == track_pk
    game_session_track.score = 1 if is_correct else -1
    game_session_track.save()

    # Check if session is complete
    if game_session_track.order == game_session.game_tracks.all().count() - 1:
        complete_session(user, "famous_tracks")


def handle_competitive_mode_submission(user, form) -> None:
    """Handle track submission for a game session of the competitive mode."""
    game_session = get_active_game_session(user, "competitive_mode")
    game_session_track = get_current_game_session_track(game_session)
    track_pk = uuid.UUID(form.cleaned_data["track"])

    # If the track has not been revealed yet, redirect to the game page
    if not game_session_track.revealed_at:
        return

    # Update track submission
    game_session_track.submitted_at = timezone.localtime()
    game_session_track.submitted_track = RaceTrack.objects.get(pk=track_pk)

    # Update score
    is_correct = game_session_track.correct_track.pk == track_pk
    if not is_correct:
        game_session_track.score = -1
    else:
        revealed_at = game_session_track.revealed_at
        submitted_at = game_session_track.submitted_at

        if revealed_at and submitted_at:
            time_difference = submitted_at - revealed_at
            if time_difference.total_seconds() < MAX_COMP_ROUND_TIME:
                game_session_track.score = (
                    MAX_COMP_ROUND_TIME - time_difference.total_seconds()
                )
            else:
                game_session_track.score = 1

    game_session_track.save()

    # Check if session is complete
    if game_session_track.order == game_session.game_tracks.all().count() - 1:
        complete_session(user, "competitive_mode")


def competitive_mode_get_segments(request) -> list[dict]:
    """Get the segments for the game session."""
    game_session = get_active_game_session(request.user, "competitive_mode")
    game_session_track = get_current_game_session_track(game_session)

    image_path = game_session_track.correct_track.image.url
    segmenter = SegmentImage(image_path, 4)
    return segmenter()
