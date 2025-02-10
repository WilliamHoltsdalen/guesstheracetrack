from django.contrib import admin
from django.utils.html import format_html

from .models import GameSession
from .models import GameSessionTrack
from .models import Hint
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
    )
    list_filter = ("user", "tracks", "is_completed")
    search_fields = ("user__username",)
    ordering = ("-start_time",)


@admin.register(GameSessionTrack)
class GameSessionTrackAdmin(admin.ModelAdmin):
    list_display = ("session", "track", "score", "order")
    list_filter = ("session", "track")
    search_fields = ("session__user__username", "track__name")
    ordering = ("session__start_time",)


@admin.register(Hint)
class HintAdmin(admin.ModelAdmin):
    list_display = ("game_session", "image_segment", "revealed_at")
    list_filter = ("game_session",)
    search_fields = ("game_session__user__username",)
    ordering = ("game_session__start_time",)
