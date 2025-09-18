# buddies/forms.py
from django import forms
from .models import BuddySession, SESSION_TYPES

class BuddySessionForm(forms.ModelForm):
    class Meta:
        model = BuddySession
        fields = ["title", "type", "start_dt", "location_name", "lat", "lon", "capacity"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g., Early swim at Bunratty"}
            ),
            # choices come from the model field; no need to pass SESSION_TYPES here
            "type": forms.Select(attrs={"class": "form-select"}),
            # IMPORTANT: this class hooks flatpickr
            "start_dt": forms.TextInput(
                attrs={
                    "class": "form-control js-datetime",
                    "placeholder": "YYYY-MM-DD HH:MM",
                    "autocomplete": "off",
                }
            ),
            "location_name": forms.TextInput(attrs={"class": "form-control"}),
            "lat": forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
            "lon": forms.NumberInput(attrs={"class": "form-control", "step": "any"}),
            "capacity": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # belt-and-braces: ensure classes exist even if widgets change later
        self.fields["title"].widget.attrs.setdefault("class", "form-control")
        self.fields["type"].widget.attrs.setdefault("class", "form-select")
        self.fields["start_dt"].widget.attrs.setdefault("class", "form-control")
        self.fields["start_dt"].widget.attrs.setdefault("data-flatpickr", "true")
        self.fields["location_name"].widget.attrs.setdefault("class", "form-control")
        self.fields["lat"].widget.attrs.setdefault("class", "form-control")
        self.fields["lon"].widget.attrs.setdefault("class", "form-control")
        self.fields["capacity"].widget.attrs.setdefault("class", "form-control")
