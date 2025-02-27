import uuid

from django.conf import settings
from django.db import models


class Score(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    score = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-score"]

    def __str__(self):
        return f"{self.user.username} - {self.score}"

    def add_game_score(self, points):
        """
        Add points from a new game to the total score
        """
        self.score += points
        self.save()
