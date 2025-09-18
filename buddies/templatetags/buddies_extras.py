# buddies/templatetags/buddies_extras.py
from django import template

register = template.Library()

BADGE_BY_TYPE = {
    "swim": "primary",
    "kayak": "info",
    "hike": "success",
    "cycle": "warning",
    "sup": "info",
    "sailing": "secondary",
    "yoga": "success",
    "sauna": "danger",
    "tour": "secondary",
    "tri": "dark",
}

@register.filter
def type_badge(value: str) -> str:
    """Return a Bootstrap color for a session type code."""
    return BADGE_BY_TYPE.get(value or "", "secondary")
