import uuid

from django.conf import settings
from django.db import models


class RaceTrack(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    image = models.ImageField(upload_to="racetracks/")
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
    tracks = models.ManyToManyField(RaceTrack, through="GameSessionTrack")
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"GameSession {self.id} - {self.user}"

    def total_score(self):
        return sum(track.score for track in self.tracks.all())


class GameSessionTrack(models.Model):
    session = models.ForeignKey(
        GameSession,
        on_delete=models.CASCADE,
        related_name="game_tracks",
    )
    track = models.ForeignKey(RaceTrack, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    order = models.IntegerField(default=0)

    class Meta:
        unique_together = ("session", "track")

    def __str__(self):
        return (
            f"GameSession {self.session.id} - {self.track.name} ({self.score} points)"
        )


class Hint(models.Model):
    game_session = models.ForeignKey(
        GameSession,
        on_delete=models.CASCADE,
        related_name="hints",
    )
    image_segment = models.ImageField(upload_to="hints/")
    revealed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Hint for {self.game_session.id}"
