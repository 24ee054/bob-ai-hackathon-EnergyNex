from django.test import TestCase, Client
from django.urls import reverse
from grid_intelligence.models import District, TelemetryRecord, GridAnomaly, DispatchDirective, ForecastRecord

class GridIntelligenceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.anand = District.objects.create(
            name="Anand & Kheda",
            city_hub="Anand / Changa",
            discom_zone="MGVCL",
            latitude=22.5645,
            longitude=72.9289,
            baseline_mw=1400.0,
            dominant_industry="Amul Dairy & CHARUSAT Zone"
        )
        self.telemetry = TelemetryRecord.objects.create(
            district=self.anand,
            timestamp="2026-09-15 08:00:00",
            demand_mw=1450.0,
            renewable_mw=320.0,
            grid_frequency_hz=49.99,
            power_factor=0.98,
            thd_pct=3.1
        )
        self.anomaly = GridAnomaly.objects.create(
            district=self.anand,
            timestamp="2026-09-15 08:00:00",
            severity="WARNING",
            root_cause="Active Feeder Surge",
            deviation_pct=18.5,
            actual_load_mw=1450.0,
            expected_load_mw=1220.0
        )
        self.directive = DispatchDirective.objects.create(
            district=self.anand,
            priority="HIGH",
            title="Anand Feeder Balance",
            action="Switch 66kV capacitor bank at Changa",
            impact="Reduces reactive load by 40 MVAR"
        )
        self.forecast = ForecastRecord.objects.create(
            district=None,
            forecast_timestamp="2026-09-15 09:00:00",
            hours_ahead="+1h",
            predicted_load_mw=18900.0,
            gbm_load_mw=18850.0,
            threshold_mw=21500.0,
            peak_alert=False
        )

    def test_district_model(self):
        self.assertEqual(str(self.anand), "Anand & Kheda (Anand / Changa) - MGVCL")
        self.assertEqual(self.anand.discom_zone, "MGVCL")

    def test_telemetry_model(self):
        self.assertEqual(self.telemetry.net_demand_mw, 1130.0)
        self.assertEqual(self.telemetry.district.name, "Anand & Kheda")

    def test_dashboard_view(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "G-EnergySense AI")
        self.assertContains(response, "Anand & Kheda")

    def test_api_live_grid(self):
        response = self.client.get(reverse('api_live_grid'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["state_total_demand_mw"], 1450.0)

    def test_api_districts(self):
        response = self.client.get(reverse('api_districts'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)

    def test_api_anomalies(self):
        response = self.client.get(reverse('api_anomalies'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 1)

    def test_api_forecast(self):
        response = self.client.get(reverse('api_forecast'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["forecast"]), 1)

    def test_api_copilot_chat(self):
        # Test general query
        payload = {"query": "Audit Anand & Kheda (CHARUSAT Zone)"}
        response = self.client.post(reverse('api_copilot_chat'), data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("CHARUSAT", data["response"])

        # Test executive brief generation
        brief_payload = {"query": "Generate SLDC Executive Incident Brief"}
        brief_response = self.client.post(reverse('api_copilot_chat'), data=brief_payload, content_type='application/json')
        self.assertEqual(brief_response.status_code, 200)
        brief_data = brief_response.json()
        self.assertIsNotNone(brief_data["markdown_brief"])
        self.assertIn("SLDC Executive", brief_data["markdown_brief"])
