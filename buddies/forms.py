from django import forms
from .models import BuddySession

class BuddySessionForm(forms.ModelForm):
    class Meta:
        model = BuddySession
        fields = ["title", "type", "start_dt", "location_name", "lat", "lon", "capacity"]
        widgets = {
            "start_dt": forms.TextInput(attrs={"data-flatpickr": "", "placeholder": "Pick date & time"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            css = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (css + " form-control").strip()
