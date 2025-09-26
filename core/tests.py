from __future__ import annotations

import json
from django.test import TestCase
from django.urls import reverse, NoReverseMatch

from core.models import Spot


class SpotsEndpointTests(TestCase):
    def setUp(self):
        Spot.objects.create(name="Test Pier", lat=52.7, lon=-8.8, type="swim")

    def _get_spots_url(self) -> str:
        # Prefer named URL if available; fall back to legacy /spots.json
        try:
            return reverse("core:spots_geojson")
        except NoReverseMatch:
            return "/spots.json"

    def test_spots_endpoint_includes_created_spot(self):
        url = self._get_spots_url()
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # Response can be a list of dicts, or GeoJSON {features:[...]}
        data = json.loads(resp.content.decode("utf-8"))
        names = []
        if isinstance(data, list):
            names = [d.get("name") for d in data]
        elif isinstance(data, dict) and "features" in data:
            names = [f.get("properties", {}).get("name") for f in data.get("features", [])]
        self.assertIn("Test Pier", names)
