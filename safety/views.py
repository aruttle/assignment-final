from __future__ import annotations

import math
from datetime import timedelta
from .tides import get_tide_extremes

import requests
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.utils import timezone


# -----------------------
# Helpers
# -----------------------
def _parse_float(val):
    try:
        return float(val)
    except Exception:
        return None


def _rate(wind_ms: float, gust_ms: float, precip_prob: int):
    """
    Simple traffic-light rules (tweak later as you like):
      Safe:    wind < 6,  gust < 9,  precip_prob < 40
      Caution: wind < 9,  gust < 12, precip_prob < 70
      Avoid:   otherwise
    """
    if wind_ms < 6 and gust_ms < 9 and precip_prob < 40:
        return "safe", "text-bg-success", "Safe conditions"
    if wind_ms < 9 and gust_ms < 12 and precip_prob < 70:
        return "caution", "text-bg-warning", "Use caution"
    return "avoid", "text-bg-danger", "Avoid today"


def _round_key(x: float, places: int = 3) -> str:
    """Round to reduce cache-key cardinality."""
    if x is None or math.isnan(x):
        return "nan"
    return f"{x:.{places}f}"


def _cache_timeout(default_seconds: int) -> int:
    return int(default_seconds)


# -----------------------
# Weather (Open-Meteo) with caching
# -----------------------
def _get_open_meteo(lat: float, lon: float):
    """
    Returns JSON from Open-Meteo. Cached per (lat, lon, hour).
    """
    now = timezone.localtime()
    hour_key = now.strftime("%Y%m%d%H")
    key = f"wx:{_round_key(lat)}:{_round_key(lon)}:{hour_key}"

    data = cache.get(key)
    if data is not None:
        return data

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "wind_speed_10m,wind_gusts_10m,precipitation",
        "hourly": "precipitation_probability",
        "timezone": "auto",
    }
    try:
        resp = requests.get(url, params=params, timeout=6)
        resp.raise_for_status()
        data = resp.json()
        cache.set(key, data, timeout=getattr(settings, "WEATHER_CACHE_TIMEOUT", _cache_timeout(600)))
        return data
    except Exception:
        return None


# -----------------------
# Tides (Stormglass) with caching — uses safety.tides.get_tide_extremes
# -----------------------
def _get_stormglass_tides(lat: float, lon: float):
    """
    Returns a list of tide extremes as dicts with *datetime* in 'time':
      [{"time": datetime, "type": "high"|"low", "height": float|None}, ...]
    Cached per (lat,lon,day). Empty list if unavailable.
    """
    # If no key, get_tide_extremes() returns 
    day_key = timezone.now().strftime("%Y%m%d")
    cache_key = f"tide:{_round_key(lat)}:{_round_key(lon)}:{day_key}"

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    res = get_tide_extremes(lat, lon, hours=48)
    items = res.get("items", [])
    # Soft-cache errors briefly 
    timeout = getattr(settings, "TIDES_CACHE_TIMEOUT", _cache_timeout(3600))
    cache.set(cache_key, items, timeout=timeout if not res.get("error") else 300)
    return items


# -----------------------
# View
# -----------------------
def safety_panel(request):
    lat = _parse_float(request.GET.get("lat"))
    lon = _parse_float(request.GET.get("lon"))
    if lat is None or lon is None:
        return HttpResponseBadRequest("Invalid coordinates")

    weather = _get_open_meteo(lat, lon)
    if not weather:
        return render(
            request,
            "safety/_panel.html",
            {"lat": lat, "lon": lon, "error": "Weather service unavailable. Try again soon."},
        )

    # Current wind & gust
    current = weather.get("current", {}) or {}
    wind_ms = float(current.get("wind_speed_10m", 0.0))
    gust_ms = float(current.get("wind_gusts_10m", 0.0))

    # Hourly precip probability for current local hour
    hourly = weather.get("hourly", {}) or {}
    times = hourly.get("time", []) or []
    probs = hourly.get("precipitation_probability", []) or []
    precip_prob = 0
    if times and probs:
        now_local = timezone.localtime()
        key = now_local.strftime("%Y-%m-%dT%H:00")
        try:
            idx = times.index(key)
            precip_prob = int(probs[idx])
        except Exception:
            precip_prob = 0

    rating, badge, label = _rate(wind_ms, gust_ms, precip_prob)

    # ---- Tides with optional calibration + future list (next 3–4) ----
    tides = _get_stormglass_tides(lat, lon)  
    future_tides = []
    time_offset = int(getattr(settings, "TIDE_TIME_OFFSET_MINUTES", 0) or 0)
    height_offset = float(getattr(settings, "TIDE_HEIGHT_OFFSET_METERS", 0.0) or 0.0)

    if tides:
        now = timezone.now()
        for e in tides:
            t = e.get("time")
            if not t or t <= now:
                continue
            item = e.copy()
            if time_offset:
                item["time"] = item["time"] + timedelta(minutes=time_offset)
            if item.get("height") is not None:
                item["height"] = item["height"] + height_offset
            future_tides.append(item)
        future_tides.sort(key=lambda x: x["time"])

    next_tide = future_tides[0] if future_tides else None

    ctx = {
        "lat": lat,
        "lon": lon,
        "wind_ms": wind_ms,
        "gust_ms": gust_ms,
        "precip_prob": precip_prob,
        "rating": rating,
        "badge": badge,
        "label": label,
        "tide_list": future_tides[:4],
        "next_tide": next_tide,
    }
    return render(request, "safety/_panel.html", ctx)
