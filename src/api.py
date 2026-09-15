"""
G-EnergySense AI — Enterprise REST API Interface
Exposes real-time SCADA telemetry, anomaly detection, and predictive forecast endpoints
for external sub-station integration, mobile dashboards, and GETCO dispatch systems.
"""

from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

from anomaly import get_latest_anomalies, load_energy_data
from bob_tools import get_current_energy_status
from forecasting import forecast_next_hours, get_forecast_model_metrics

def api_get_live_grid_summary():
    """Endpoint: GET /api/v1/grid/live"""
    status = get_current_energy_status()
    metrics = get_forecast_model_metrics()
    return {
        "status": "success",
        "timestamp": status["timestamp"],
        "state_total_demand_mw": status["total_state_demand_mw"],
        "state_renewable_mw": status["total_renewable_mw"],
        "grid_frequency_hz": status["grid_frequency_hz"],
        "model_accuracy_mape": f"{metrics['mape_pct']}%"
    }

def api_get_active_anomalies(limit=5):
    """Endpoint: GET /api/v1/anomalies/active"""
    anoms = get_latest_anomalies(limit=limit)
    out = []
    for _, r in anoms.iterrows():
        out.append({
            "timestamp": str(r["timestamp"]),
            "district": r.get("district", "Unknown"),
            "demand_mw": float(r["demand_mw"]),
            "expected_mw": float(r["expected_load"]),
            "deviation_pct": float(r["deviation_pct"]),
            "severity": r["severity"],
            "root_cause": r.get("root_cause", "Unscheduled Draw")
        })
    return {"status": "success", "count": len(out), "anomalies": out}

def api_get_forecast(hours=4):
    """Endpoint: GET /api/v1/forecast/upcoming"""
    fc = forecast_next_hours(hours_ahead=hours)
    out = []
    for _, r in fc.iterrows():
        out.append({
            "hours_ahead": r["hours_ahead"],
            "timestamp": r["timestamp"].strftime("%H:%M"),
            "predicted_load_mw": float(r["predicted_load_mw"]),
            "peak_alert": bool(r["peak_alert"])
        })
    return {"status": "success", "forecast": out}

if __name__ == "__main__":
    print("API Live Summary:", api_get_live_grid_summary())
    print("API Active Anomalies:", api_get_active_anomalies(2))
