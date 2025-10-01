from django.shortcuts import render
from django.http import JsonResponse, HttpResponse

from .models import Spot

try:
    from activities.models import Activity
    HAS_ACTIVITIES = True
except Exception:
    HAS_ACTIVITIES = False


def home(request):
    """Home page with the map + HTMX loaders."""
    return render(request, "core/home.html")


def pulse(request):
    """Tiny HTMX round-trip check."""
    return HttpResponse("Working!")


def spots_geojson(request):
    """
    Returns active spots as JSON for Leaflet.
    If Activities app is present and linked via Activity.spot, also include
    a list of activities per spot.
    """
    spots = list(Spot.objects.filter(is_active=True).order_by("name"))

    by_spot = {}
    if HAS_ACTIVITIES and spots:
        acts = Activity.objects.filter(spot__in=spots).values("id", "title", "spot_id")
        for a in acts:
            by_spot.setdefault(a["spot_id"], []).append(
                {"id": a["id"], "title": a["title"]}
            )

    data = []
    for s in spots:
        item = {
            "id": s.id,
            "name": s.name,
            "lat": float(s.lat),  # Decimal → float for JSON
            "lon": float(s.lon),
            "type": s.type,
        }
        if HAS_ACTIVITIES:
            item["activities"] = by_spot.get(s.id, [])
        data.append(item)

    return JsonResponse(data, safe=False)

