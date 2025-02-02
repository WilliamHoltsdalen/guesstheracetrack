from django import forms

from .models import RaceTrack


class TrackChoiceForm(forms.Form):
    all_pks = list(RaceTrack.objects.values_list("pk", flat=True))

    track = forms.ChoiceField(
        choices=[(pk, RaceTrack.objects.get(pk=pk).name) for pk in all_pks],
    )
