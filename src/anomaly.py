import os
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

DATA_PATH = Path(__file__).resolve().parent / "data" / "gujarat_grid_data.csv"

def load_energy_data(csv_path=None):
    path = Path(csv_path) if csv_path else DATA_PATH
    if not path.exists():
        from data.generate_gujarat_data import generate_gujarat_grid_dataset
        return generate_gujarat_grid_dataset()
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

class EnergyAnomalyDetector:
    """
    Advanced Grid Anomaly Engine with Multi-Variate Isolation Forest
    and Root-Cause Physical Attribution.
    """
    def __init__(self, contamination=0.035, random_state=42):
        self.model = IsolationForest(contamination=contamination, random_state=random_state)
        
    def fit_and_detect(self, df):
        data = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(data["timestamp"]):
            data["timestamp"] = pd.to_datetime(data["timestamp"])
            
        data["hour"] = data["timestamp"].dt.hour
        group_key = "district" if "district" in data.columns else "discom_zone"
        
        # Expected baseline
        group_medians = data.groupby([group_key, "hour"])["demand_mw"].transform("median")
        data["expected_load"] = group_medians
        data["expected_kw"] = data["expected_load"] * 1000.0
        
        feature_cols = ["demand_mw", "grid_frequency_hz", "power_factor", "hour"]
        if "thd_pct" in data.columns:
            feature_cols.append("thd_pct")
            
        X = data[feature_cols].values
        preds = self.model.fit_predict(X)
        
        data["deviation_pct"] = ((data["demand_mw"] - data["expected_load"]) / data["expected_load"].replace(0, 1)) * 100.0
        data["is_anomaly"] = (preds == -1) & ((data["deviation_pct"] > 16.0) | (data.get("thd_pct", 0) > 6.0))
        
        def assign_sev_and_cause(row):
            if not row["is_anomaly"]:
                return "NORMAL", "Nominal"
            dev = row["deviation_pct"]
            thd = row.get("thd_pct", 3.0)
            freq = row.get("grid_frequency_hz", 50.0)
            pf = row.get("power_factor", 0.98)
            
            # Root Cause Attribution
            causes = []
            if dev >= 25.0:
                causes.append("Active Load Surge")
            if thd >= 5.5:
                causes.append(f"Non-Linear Harmonics (THD {thd:.1f}%)")
            if pf < 0.95:
                causes.append(f"Inductive Reactive Drain (PF {pf:.2f})")
            if freq < 49.92:
                causes.append(f"System Frequency Sag ({freq:.3f} Hz)")
                
            cause_str = " + ".join(causes) if causes else "Unscheduled Draw"
            
            if dev >= 35.0 or freq < 49.91 or thd >= 7.0:
                return "CRITICAL", cause_str
            elif dev >= 22.0 or thd >= 5.5:
                return "HIGH", cause_str
            else:
                return "WARNING", cause_str
                
        res = data.apply(assign_sev_and_cause, axis=1)
        data["severity"] = [r[0] for r in res]
        data["root_cause"] = [r[1] for r in res]
        data["actual_load"] = data["demand_mw"]
        return data

def detect_anomalies(df=None):
    if df is None:
        df = load_energy_data()
    detector = EnergyAnomalyDetector()
    return detector.fit_and_detect(df)

def get_latest_anomalies(csv_path=None, limit=10):
    scored = detect_anomalies(load_energy_data(csv_path))
    anoms = scored[scored["is_anomaly"]].sort_values("timestamp", ascending=False)
    return anoms.head(limit)

if __name__ == "__main__":
    anoms = get_latest_anomalies()
    print(f"Detected {len(anoms)} anomalies:")
    for _, r in anoms.iterrows():
        dist = r.get("district", "Region")
        print(f"[{r['severity']}] {r['timestamp']} | {dist} | Load: {r['demand_mw']} MW (+{r['deviation_pct']:.1f}%) | Cause: {r['root_cause']}")
