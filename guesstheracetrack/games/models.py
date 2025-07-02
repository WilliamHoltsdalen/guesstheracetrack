import uuid

from django.conf import settings
from django.db import models

from .utils import RandomFileName


class RaceTrack(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to=RandomFileName("racetracks"))
    difficulty = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class GameSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    game_type = models.CharField(max_length=255, default="")

    def __str__(self):
        return f"{self.user} - {self.game_type} - {self.score} points"


class GameSessionTrack(models.Model):
    session = models.ForeignKey(
        GameSession,
        on_delete=models.CASCADE,
        related_name="game_tracks",
    )
    correct_track = models.ForeignKey(
        RaceTrack,
        on_delete=models.CASCADE,
        related_name="correct_track",
        default=None,
    )
    incorrect_track_1 = models.ForeignKey(
        RaceTrack,
        on_delete=models.CASCADE,
        related_name="incorrect_track_1",
        default=None,
    )
    incorrect_track_2 = models.ForeignKey(
        RaceTrack,
        on_delete=models.CASCADE,
        related_name="incorrect_track_2",
        default=None,
    )
    score = models.IntegerField(default=0)
    order = models.IntegerField(default=0)
    revealed_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_track = models.ForeignKey(
        RaceTrack,
        on_delete=models.CASCADE,
        related_name="submitted_track",
        default=None,
        null=True,
    )

    class Meta:
        unique_together = (
            "session",
            "correct_track",
            "incorrect_track_1",
            "incorrect_track_2",
        )

    def __str__(self):
        return (
            f"GameSession {self.session.id} - Correct:"
            f" {self.correct_track.name}, Incorrect 1: "
            f"{self.incorrect_track_1.name}, Incorrect 2: "
            f"{self.incorrect_track_2.name} ({self.score} points)"
        )
