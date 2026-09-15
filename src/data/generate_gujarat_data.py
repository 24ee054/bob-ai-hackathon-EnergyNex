import os
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

GUJARAT_DATA_PATH = Path(__file__).resolve().parent / "gujarat_grid_data.csv"
LEGACY_DATA_PATH = Path(__file__).resolve().parent / "energy_data.csv"

def generate_gujarat_grid_dataset(days=7, interval_minutes=15, seed=42, end_time=None):
    if seed is not None:
        np.random.seed(seed)
        
    if end_time is None:
        now = datetime.now()
        minute_floor = (now.minute // interval_minutes) * interval_minutes
        end_time = now.replace(minute=minute_floor, second=0, microsecond=0)
        
    start_time = end_time - timedelta(days=days)
    timestamps = pd.date_range(start=start_time, end=end_time, freq=f"{interval_minutes}min")
    
    # 10 Key Gujarat Districts & City Hubs
    districts = [
        {"district": "Ahmedabad", "city": "Ahmedabad Metro", "discom": "UGVCL (North Gujarat)", "base_mw": 2800, "peak_add": 1200, "base_thd": 3.8, "pf": 0.975},
        {"district": "Surat", "city": "Surat Industrial", "discom": "DGVCL (South Gujarat)", "base_mw": 3100, "peak_add": 1400, "base_thd": 5.4, "pf": 0.960},
        {"district": "Vadodara", "city": "Vadodara City", "discom": "MGVCL (Central Gujarat)", "base_mw": 1400, "peak_add": 650, "base_thd": 3.5, "pf": 0.980},
        {"district": "Rajkot", "city": "Rajkot City", "discom": "PGVCL (Saurashtra & Kutch)", "base_mw": 1300, "peak_add": 700, "base_thd": 4.9, "pf": 0.965},
        {"district": "Anand & Kheda", "city": "Anand (CHARUSAT Zone)", "discom": "MGVCL (Central Gujarat)", "base_mw": 900, "peak_add": 420, "base_thd": 3.2, "pf": 0.982},
        {"district": "Gandhinagar", "city": "GIFT City / Capital", "discom": "UGVCL (North Gujarat)", "base_mw": 850, "peak_add": 480, "base_thd": 2.8, "pf": 0.990},
        {"district": "Kutch", "city": "Bhuj / Mundra", "discom": "PGVCL (Saurashtra & Kutch)", "base_mw": 1600, "peak_add": 850, "base_thd": 4.1, "pf": 0.970},
        {"district": "Bharuch", "city": "Ankleshwar / Dahej", "discom": "DGVCL (South Gujarat)", "base_mw": 1800, "peak_add": 750, "base_thd": 5.8, "pf": 0.955},
        {"district": "Jamnagar", "city": "Jamnagar City", "discom": "PGVCL (Saurashtra & Kutch)", "base_mw": 1700, "peak_add": 700, "base_thd": 4.3, "pf": 0.972},
        {"district": "Bhavnagar", "city": "Bhavnagar City", "discom": "PGVCL (Saurashtra & Kutch)", "base_mw": 750, "peak_add": 380, "base_thd": 4.5, "pf": 0.968}
    ]
    
    records = []
    last_24h_start = end_time - timedelta(hours=24)
    
    for ts in timestamps:
        hour = ts.hour + ts.minute / 60.0
        is_weekend = ts.weekday() >= 5
        is_in_last_24h = ts >= last_24h_start
        
        # Gujarat dual-peak curve
        day_peak = np.exp(-((hour - 14.5) ** 2) / (2 * (3.5 ** 2)))
        eve_peak = 0.85 * np.exp(-((hour - 20.0) ** 2) / (2 * (2.0 ** 2)))
        combined_curve = np.maximum(day_peak, eve_peak)
        
        night_factor = 0.55 if (hour < 5 or hour > 23) else 1.0
        weekend_factor = 0.82 if is_weekend else 1.0
        hours_from_end = (end_time - ts).total_seconds() / 3600.0
        
        # Grid frequency (nominal 50.00 Hz)
        freq_hz = float(50.01 + np.random.normal(0, 0.02))
        
        for d in districts:
            d_name = d["district"]
            base = d["base_mw"] + (d["peak_add"] * combined_curve * night_factor * weekend_factor)
            mw = max(200.0, base + np.random.normal(0, d["base_mw"] * 0.025))
            thd = float(np.clip(d["base_thd"] + np.random.normal(0, 0.3), 1.5, 9.5))
            pf = float(np.clip(d["pf"] + np.random.normal(0, 0.006), 0.91, 0.995))
            
            # Anomalies in last 24h
            if d_name == "Surat" and 6 <= hours_from_end <= 10:
                mw *= 1.42  # Active power spike
                thd += 2.8   # Severe harmonic distortion from power electronics
                pf -= 0.04   # Inductive reactive drain
                freq_hz = 49.88
            elif d_name == "Anand & Kheda" and 14 <= hours_from_end <= 17:
                mw *= 1.35  # Agro seasonal pump synchronization
            elif d_name == "Bharuch" and 18 <= hours_from_end <= 20:
                mw *= 1.30  # Petrochemical corridor shift surge
                thd += 2.2
                
            is_kutch = d_name == "Kutch"
            solar_mw = max(0.0, (2800.0 if is_kutch else 220.0) * np.exp(-((hour - 13.0) ** 2) / (2 * (2.8 ** 2))))
            wind_mw = max(15.0, (1400.0 if is_kutch else 75.0) + np.random.normal(0, 30.0))
            re_total = solar_mw + wind_mw
            net_demand_mw = max(50.0, mw - re_total)
            
            # Reactive power MVAR: Q = P * tan(acos(PF))
            phi = np.arccos(pf)
            mvar = mw * np.tan(phi)
            
            # CERC Deviation Settlement Mechanism (DSM) Penalty Risk (Rs / MWh)
            # Under 49.90 Hz, heavy penalty incurred for overdraw
            dsm_rate_inr = 8500.0 if freq_hz < 49.90 else (2400.0 if freq_hz < 49.95 else 0.0)
            
            records.append({
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "district": d_name,
                "city_hub": d["city"],
                "discom_zone": d["discom"],
                "panel_name": d_name,
                "demand_mw": round(mw, 2),
                "net_demand_mw": round(net_demand_mw, 2),
                "active_power_kw": round(mw * 1000.0, 1),
                "reactive_power_mvar": round(mvar, 2),
                "renewable_mw": round(re_total, 2),
                "solar_mw": round(solar_mw, 2),
                "wind_mw": round(wind_mw, 2),
                "grid_frequency_hz": round(freq_hz, 3),
                "voltage_kv": round(400.0 + np.random.uniform(-3.5, 3.5), 1),
                "power_factor": round(pf, 3),
                "thd_pct": round(thd, 2),
                "dsm_penalty_rate_inr": dsm_rate_inr
            })
            
    df = pd.DataFrame(records)
    GUJARAT_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(GUJARAT_DATA_PATH, index=False)
    df.to_csv(LEGACY_DATA_PATH, index=False)
    print(f"Generated {len(df)} records across 10 districts with advanced telemetry saved to {GUJARAT_DATA_PATH}")
    return df

if __name__ == "__main__":
    generate_gujarat_grid_dataset()
