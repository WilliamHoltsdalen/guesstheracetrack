from django.contrib import admin
from django.utils.html import format_html

from .models import RaceTrack


@admin.register(RaceTrack)
class RaceTrackAdmin(admin.ModelAdmin):
    list_display = ("name", "difficulty", "created_at", "image_preview")

    @admin.display(
        description="Preview",
    )
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100px">', obj.image_url)
        return "(No image)"
