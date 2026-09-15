import os
import sys
import unittest
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from anomaly import detect_anomalies, load_energy_data
from forecasting import forecast_next_hours, get_forecast_model_metrics
from recommendations import generate_recommendations
from bob_tools import get_current_energy_status
from api import api_get_live_grid_summary, api_get_active_anomalies, api_get_forecast

class TestGEnergySenseAI(unittest.TestCase):
    def setUp(self):
        self.df = load_energy_data()
        
    def test_dataset_integrity(self):
        self.assertFalse(self.df.empty, "Dataset must not be empty")
        required_cols = ["timestamp", "district", "demand_mw", "renewable_mw", "grid_frequency_hz"]
        for col in required_cols:
            self.assertIn(col, self.df.columns, f"Missing required column: {col}")
            
    def test_anomaly_detection(self):
        scored = detect_anomalies(self.df.tail(200))
        self.assertIn("is_anomaly", scored.columns)
        self.assertIn("severity", scored.columns)
        self.assertIn("root_cause", scored.columns)
        
    def test_forecasting_output(self):
        fc = forecast_next_hours(hours_ahead=4, df=self.df)
        self.assertEqual(len(fc), 4)
        self.assertIn("predicted_load_mw", fc.columns)
        self.assertTrue(all(fc["predicted_load_mw"] > 100.0))
        
    def test_recommendations_engine(self):
        recs = generate_recommendations()
        self.assertTrue(len(recs) > 0, "Recommendations engine must produce directives")
        
    def test_bob_tools_status(self):
        status = get_current_energy_status()
        self.assertIn("total_state_demand_mw", status)
        self.assertGreater(status["total_state_demand_mw"], 5000.0)

    def test_enterprise_api_endpoints(self):
        live_res = api_get_live_grid_summary()
        self.assertEqual(live_res["status"], "success")
        self.assertIn("state_total_demand_mw", live_res)

        anom_res = api_get_active_anomalies(limit=3)
        self.assertEqual(anom_res["status"], "success")
        self.assertIn("anomalies", anom_res)

        fc_res = api_get_forecast(hours=2)
        self.assertEqual(fc_res["status"], "success")
        self.assertEqual(len(fc_res["forecast"]), 2)

if __name__ == "__main__":
    unittest.main()
