import requests
from django.shortcuts import render
from django.http import HttpResponseBadRequest
from django.utils import timezone

def _parse_float(param):
    try:
        return float(param)
    except Exception:
        return None

def _rate(wind_ms: float, gust_ms: float, precip_prob: int):
    """
    Simple traffic-light rules:
    Safe:    wind < 6,  gust < 9,  precip_prob < 40
    Caution: wind < 9,  gust < 12, precip_prob < 70
    Avoid:   otherwise
    """
    if wind_ms < 6 and gust_ms < 9 and precip_prob < 40:
        return "safe", "text-bg-success", "Safe conditions"
    if wind_ms < 9 and gust_ms < 12 and precip_prob < 70:
        return "caution", "text-bg-warning", "Use caution"
    return "avoid", "text-bg-danger", "Avoid today"

def safety_panel(request):
    lat = _parse_float(request.GET.get("lat"))
    lon = _parse_float(request.GET.get("lon"))
    if lat is None or lon is None:
        return HttpResponseBadRequest("Invalid coordinates")

    # Open-Meteo 
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "wind_speed_10m,wind_gusts_10m,precipitation",
        "hourly": "precipitation_probability",
        "timezone": "auto",
    }

    try:
        r = requests.get(url, params=params, timeout=6)
        r.raise_for_status()
        data = r.json()
    except Exception:
        # Fallback
        ctx = {
            "lat": lat, "lon": lon, "error": "Weather service unavailable. Try again soon."
        }
        return render(request, "safety/_panel.html", ctx)

    # Extract current wind & gust
    current = data.get("current", {})
    wind_ms = float(current.get("wind_speed_10m", 0.0))
    gust_ms = float(current.get("wind_gusts_10m", 0.0))

    # Find precip probability for the current local hour
    hourly = data.get("hourly", {})
    times = hourly.get("time", []) or []
    probs = hourly.get("precipitation_probability", []) or []
    precip_prob = 0
    if times and probs:
        # Open-Meteo returns times like "YYYY-MM-DDTHH:00"
        now = timezone.localtime()
        key = now.strftime("%Y-%m-%dT%H:00")
        try:
            idx = times.index(key)
        except ValueError:
            idx = 0
        try:
            precip_prob = int(probs[idx])
        except Exception:
            precip_prob = 0

    rating, badge, label = _rate(wind_ms, gust_ms, precip_prob)

    ctx = {
        "lat": lat,
        "lon": lon,
        "wind_ms": wind_ms,
        "gust_ms": gust_ms,
        "precip_prob": precip_prob,
        "rating": rating,
        "badge": badge,
        "label": label,
    }
    return render(request, "safety/_panel.html", ctx)
