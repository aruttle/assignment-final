from __future__ import annotations
import os
import datetime as dt
import requests
from django.conf import settings

API_KEY = getattr(settings, "STORMGLASS_API_KEY", os.environ.get("STORMGLASS_API_KEY", ""))

def get_tide_extremes(lat: float, lon: float, hours: int = 36) -> dict:
    """
    Returns {"items":[{"time": datetime, "type":"high|low", "height": float|None}], "error": str|None}
    Uses Stormglass: https://api.stormglass.io/v2/tide/extremes/point
    """
    if not API_KEY:
        return {"items": [], "error": "no-api-key"}

    start = dt.datetime.utcnow()
    end = start + dt.timedelta(hours=hours)

    url = "https://api.stormglass.io/v2/tide/extremes/point"
    params = {
        "lat": lat,
        "lng": lon,
        "start": int(start.timestamp()),
        "end": int(end.timestamp()),
    }
    headers = {"Authorization": API_KEY}

    try:
        r = requests.get(url, params=params, headers=headers, timeout=8)
        r.raise_for_status()
        data = r.json().get("data", [])
        items = []
        for x in data:
            # "time" is ISO 8601 with Z; convert to aware datetime
            t = x.get("time")
            if not t:
                continue
            if t.endswith("Z"):
                t = t[:-1] + "+00:00"
            when = dt.datetime.fromisoformat(t)
            items.append({
                "time": when,
                "type": x.get("type"),       # "high" or "low"
                "height": x.get("height"),   
            })
        return {"items": items, "error": None}
    except Exception as e:
        return {"items": [], "error": str(e)}
