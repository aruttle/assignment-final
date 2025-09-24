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
    """
    Return a Bootstrap color token (e.g. 'primary') for a session type code.
    Usage: class="badge text-bg-{{ s.type|type_badge }}"
    """
    return BADGE_BY_TYPE.get(value or "", "secondary")


@register.filter
def type_badge_class(value: str) -> str:
    """
    Return a full Bootstrap badge class for convenience.
    Usage: class="badge rounded-pill {{ s.type|type_badge_class }}"
    """
    return f"text-bg-{BADGE_BY_TYPE.get(value or '', 'secondary')}"


@register.filter
def attr(obj, name):
    """
    Template helper: return getattr(obj, name, None).
    Useful when the date/time field name varies (e.g., 'start_dt' vs 'start_time').
    """
    try:
        return getattr(obj, name)
    except Exception:
        return None
