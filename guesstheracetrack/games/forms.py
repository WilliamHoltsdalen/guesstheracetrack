from django import forms

from .models import RaceTrack


class TrackChoiceForm(forms.Form):
    track = forms.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        all_pks = list(RaceTrack.objects.values_list("pk", flat=True))
        self.fields["track"].choices = [
            (pk, RaceTrack.objects.get(pk=pk).name) for pk in all_pks
        ]
