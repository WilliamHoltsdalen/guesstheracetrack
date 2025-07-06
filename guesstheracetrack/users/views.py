from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView
from django.views.generic.edit import DeleteView

from guesstheracetrack.games.models import GameSession
from guesstheracetrack.games.models import GameSessionTrack
from guesstheracetrack.users.forms import UserUpdateForm
from guesstheracetrack.users.models import User

# Maximum time (in seconds) for a guess to be considered valid for average calculation
MAX_GUESS_TIME = 60


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "id"
    slug_url_kwarg = "id"

    def get_context_data(self, **kwargs):
        """Add custom context data to the template."""
        context = super().get_context_data(**kwargs)

        # Add custom context here
        user = self.get_object()

        # Calculate user statistics from actual models
        games = GameSession.objects.filter(user=user, is_completed=True)
        games_played = games.count()
        tracks = GameSessionTrack.objects.filter(
            session__user=user,
            submitted_at__isnull=False,
        )
        tracks_guessed = tracks.count()

        # Get best score
        highest_score_session = (
            GameSession.objects.filter(user=user, is_completed=True)
            .order_by("-score")
            .first()
        )
        highest_score = highest_score_session.score if highest_score_session else 0

        # Calculate average guess time for tracks
        suitable_tracks = tracks.filter(
            submitted_at__isnull=False,
            revealed_at__isnull=False,
        )
        track_count = suitable_tracks.count()
        if track_count > 0:
            total_time = 0
            for track in suitable_tracks:
                if track.revealed_at and track.submitted_at:
                    time_diff = (track.submitted_at - track.revealed_at).total_seconds()
                    if time_diff < MAX_GUESS_TIME:
                        total_time += time_diff

            avg_guess_time = round(total_time / track_count, 2)
        else:
            avg_guess_time = 0

        # Get recent games
        recent_games = GameSession.objects.filter(
            user=user,
            is_completed=True,
            end_time__isnull=False,
        ).order_by("-end_time")[:5]

        # Add to context
        context["games_played"] = games_played
        context["tracks_guessed"] = tracks_guessed
        context["highest_score"] = highest_score
        context["avg_guess_time"] = avg_guess_time
        context["recent_games"] = recent_games

        return context


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "users/user_form.html"
    success_message = _("Information successfully updated")

    def get_success_url(self) -> str:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.get_absolute_url()

    def get_object(self, queryset: QuerySet | None = None) -> User:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        return reverse("users:detail", kwargs={"pk": self.request.user.pk})


user_redirect_view = UserRedirectView.as_view()


class UserDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = "users/user_confirm_delete.html"
    success_url = reverse_lazy("account_logout")  # Log out after deletion

    def get_object(self, queryset=None):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Your account has been deleted.")
        return super().delete(request, *args, **kwargs)


@login_required
def reset_progress_view(request):
    if request.method == "POST":
        GameSession.objects.filter(user=request.user).delete()
        messages.success(request, "Your game progress has been reset.")
        return redirect("users:detail", pk=request.user.pk)
    return render(request, "users/user_confirm_reset.html")
