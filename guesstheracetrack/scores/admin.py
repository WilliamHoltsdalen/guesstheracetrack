from django.contrib import admin

from .models import Score


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ("user", "score", "updated_at")
    list_filter = ("user",)
    search_fields = ("user__username",)
    ordering = ("-score",)
