import uuid

from django.db import models
from users.models import User


class Score(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
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
