from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse

class SafetyPanelTests(TestCase):
    @patch("safety.views.requests.get")
    def test_safety_panel_renders_rating(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "current": {"wind_speed_10m": 4.5, "wind_gusts_10m": 6.0, "precipitation": 0.0},
            "hourly": {
                "time": ["2099-01-01T00:00"],
                "precipitation_probability": [10],
            },
        }
        c = Client()
        resp = c.get("/safety/panel/", {"lat": "52.7", "lon": "-8.8"})
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn("Safety check", html)
        # with low wind/gust/precip, expect "Safe"
        self.assertIn("Safe conditions", html)
