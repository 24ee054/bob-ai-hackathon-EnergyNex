import os
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from pathlib import Path
from datetime import datetime
import pandas as pd

from anomaly import load_energy_data, get_latest_anomalies
from forecasting import forecast_next_hours
from recommendations import generate_recommendations

def get_current_energy_status(district=None):
    df = load_energy_data()
    max_t = df["timestamp"].max()
    rows = df[df["timestamp"] == max_t]
    
    if district and district not in ("All Gujarat (Statewide)", "All Gujarat", "All Districts"):
        rows = rows[rows["district"] == district]
        
    total_mw = rows["demand_mw"].sum()
    total_ren = rows["renewable_mw"].sum()
    avg_freq = rows["grid_frequency_hz"].mean()
    avg_pf = rows["power_factor"].mean()
    
    dist_map = {}
    for _, r in rows.iterrows():
        d_name = r.get("district", r.get("discom_zone"))
        dist_map[d_name] = {
            "city": r.get("city_hub", ""),
            "discom": r.get("discom_zone", ""),
            "demand_mw": float(r["demand_mw"]),
            "renewable_mw": float(r["renewable_mw"]),
            "frequency_hz": float(r["grid_frequency_hz"])
        }
        
    return {
        "timestamp": str(max_t),
        "total_state_demand_mw": round(total_mw, 1),
        "total_load_kw": round(total_mw * 1000.0, 1),
        "total_renewable_mw": round(total_ren, 1),
        "renewable_share_pct": round((total_ren / max(total_mw, 1)) * 100, 1),
        "grid_frequency_hz": round(avg_freq, 3),
        "average_pf": round(avg_pf, 3),
        "districts": dist_map
    }

def generate_facility_report(district=None):
    status = get_current_energy_status(district)
    anomalies = get_latest_anomalies(limit=4)
    if district and district not in ("All Gujarat (Statewide)", "All Gujarat"):
        anomalies = anomalies[anomalies["district"] == district]
        
    forecast = forecast_next_hours(panel_name=district or "All Gujarat (Statewide)")
    recs = generate_recommendations(anomalies, forecast, selected_scope=district or "All Gujarat (Statewide)")
    
    scope_name = f"{district} District" if (district and district not in ("All Gujarat (Statewide)", "All Gujarat")) else "Whole Gujarat State Grid"
    
    lines = [
        f"### ⚡ SLDC Operational Intelligence Brief — {scope_name}",
        f"**System Timestamp:** `{status['timestamp']}` | **Copilot:** IBM Bob Grid Intelligence",
        f"**Monitored Active Demand:** `{status['total_state_demand_mw']:,} MW` | **Grid Frequency:** `{status['grid_frequency_hz']} Hz` | **Renewable Share:** `{status['renewable_share_pct']}%`\n",
        "#### 1. Live District & City Telemetry"
    ]
    
    for d_name, d_data in list(status["districts"].items())[:6]:
        lines.append(f"- **{d_name} ({d_data['city']})** [{d_data['discom']}]: `{d_data['demand_mw']:,} MW` (Renewable: `{d_data['renewable_mw']:,} MW`)")
        
    lines.append("\n#### 2. Active District Anomalies & Feeder Surges")
    if anomalies is not None and not anomalies.empty:
        for _, a in anomalies.head(2).iterrows():
            d = a.get("district", "Unknown")
            c = a.get("city_hub", "")
            lines.append(f"- **[{a['severity']}] {d} ({c})**: Recorded `{a['demand_mw']:,} MW` vs Expected `{a['expected_load']:.1f} MW` (**+{a['deviation_pct']:.1f}% surge**)")
    else:
        lines.append("- All territorial feeders operating within seasonal limits.")
        
    lines.append("\n#### 3. Short-Term Predictive Load Forecast (Next 4h)")
    for _, f in forecast.iterrows():
        t_str = f["timestamp"].strftime("%H:%M")
        lines.append(f"- `{t_str}`: `{f['predicted_load_mw']:,} MW` [{f['status']}]")
        
    lines.append("\n#### 4. Actionable SLDC Dispatch Directives")
    for r in recs:
        lines.append(f"- **[{r['priority']}] {r['title']}**\n  👉 *Action:* {r['action']}\n  📈 *Grid Impact:* {r['impact']}")
        
    return "\n".join(lines)

if __name__ == "__main__":
    print(generate_facility_report())
