from django.contrib import admin
from django.utils.html import format_html

from .models import GameSession
from .models import GameSessionTrack
from .models import RaceTrack


@admin.register(RaceTrack)
class RaceTrackAdmin(admin.ModelAdmin):
    list_display = ("name", "difficulty", "created_at", "image_preview")

    @admin.display(
        description="Preview",
    )
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100px">', obj.image.url)
        return "(No image)"


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "start_time",
        "end_time",
        "score",
        "is_completed",
        "game_type",
    )
    list_filter = ("user", "is_completed")
    search_fields = ("user__username",)
    ordering = ("-start_time",)


@admin.register(GameSessionTrack)
class GameSessionTrackAdmin(admin.ModelAdmin):
    list_display = (
        "session",
        "correct_track",
        "incorrect_track_1",
        "incorrect_track_2",
        "score",
        "order",
        "revealed_at",
        "submitted_at",
        "submitted_track",
    )
    list_filter = ("session", "correct_track")
    search_fields = ("session__user__username", "correct_track__name")
    ordering = ("session__start_time",)
