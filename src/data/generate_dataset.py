"""
Dataset Generator for EnergySense AI

Generates a realistic 7-day electrical energy consumption dataset with 15-minute
intervals across three sub-panels:
  - 'Lighting Panel' (Baseline: 2–6 kW; high from 08:00 to 20:00, low overnight)
  - 'Power Panel' (Baseline: 5–12 kW; office equipment/machinery during work hours)
  - 'HVAC / AC Panel' (Baseline: 8–20 kW; weather/occupancy dependent, peaks 12:00–16:00)

Columns:
  - timestamp (YYYY-MM-DD HH:MM:SS)
  - panel_name (str)
  - voltage_v (nominal 230V with random noise +-4V)
  - current_a (calculated: (P * 1000) / (V * PF))
  - active_power_kw (float, 2 decimal places)
  - reactive_power_kvar (float, 2 decimal places)
  - power_factor (float between 0.88 and 0.98)

Intentional Anomalies in the last 24 hours:
  - Anomaly 1 (HVAC Spike): HVAC Panel consumption surges to +55% above baseline between 13:00 and 15:00.
  - Anomaly 2 (Overnight Waste): Lighting Panel draws 5.2 kW at 02:30 AM (normally 0.8 kW).
"""

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

DATA_PATH = Path(__file__).resolve().parent / "energy_data.csv"


def generate_energy_dataset(
    days: int = 7,
    interval_minutes: int = 15,
    seed: int = 42,
    end_time: datetime | None = None,
) -> pd.DataFrame:
    """Generate realistic 7-day electrical telemetry dataset with 15-minute frequency."""
    if seed is not None:
        np.random.seed(seed)

    if end_time is None:
        now = datetime.now()
        minute_floor = (now.minute // interval_minutes) * interval_minutes
        end_time = now.replace(minute=minute_floor, second=0, microsecond=0)

    start_time = end_time - timedelta(days=days)
    timestamps = pd.date_range(
        start=start_time, end=end_time, freq=f"{interval_minutes}min"
    )

    panels = [
        "Lighting Panel",
        "Power Panel",
        "HVAC / AC Panel",
    ]

    records = []
    last_24h_start = end_time - timedelta(hours=24)

    for ts in timestamps:
        hour_float = ts.hour + ts.minute / 60.0
        is_weekend = ts.weekday() >= 5
        is_in_last_24h = ts >= last_24h_start

        # Nominal 230V with random noise +/- 4V
        voltage_noise = np.random.uniform(-4.0, 4.0)
        voltage_v = round(230.0 + voltage_noise, 2)

        for panel in panels:
            # Power factor between 0.88 and 0.98
            if panel == "Lighting Panel":
                pf = round(float(np.random.uniform(0.92, 0.98)), 3)
            elif panel == "Power Panel":
                pf = round(float(np.random.uniform(0.89, 0.96)), 3)
            else:  # HVAC / AC Panel
                pf = round(float(np.random.uniform(0.88, 0.94)), 3)

            day_mult = 0.75 if is_weekend else 1.0

            # 1. Lighting Panel: Baseline 2–6 kW; high from 08:00 to 20:00, low overnight (~0.8 kW)
            if panel == "Lighting Panel":
                if 8.0 <= hour_float < 20.0:
                    base_kw = 5.2 * day_mult + np.random.normal(0, 0.35)
                else:
                    base_kw = 0.85 + np.random.normal(0, 0.08)
                base_kw = float(np.clip(base_kw, 0.7, 6.5))

            # 2. Power Panel: Baseline 5–12 kW; office equipment/machinery during work hours
            elif panel == "Power Panel":
                if 8.0 <= hour_float < 18.0:
                    base_kw = 10.5 * day_mult + np.random.normal(0, 0.75)
                else:
                    base_kw = 5.2 + np.random.normal(0, 0.25)
                base_kw = float(np.clip(base_kw, 4.8, 12.8))

            # 3. HVAC / AC Panel: Baseline 8–20 kW; peaks 12:00–16:00
            else:
                if 12.0 <= hour_float < 16.0:
                    base_kw = 18.2 * day_mult + np.random.normal(0, 0.9)
                elif 8.0 <= hour_float < 19.0:
                    base_kw = 13.5 * day_mult + np.random.normal(0, 0.8)
                else:
                    base_kw = 8.4 + np.random.normal(0, 0.3)
                base_kw = float(np.clip(base_kw, 7.5, 20.5))

            # Intentional Anomalies in the last 24 hours:
            # Anomaly 1: HVAC Panel consumption surges +55% between 13:00 and 15:00
            if is_in_last_24h and panel == "HVAC / AC Panel":
                if 13.0 <= hour_float < 15.0:
                    base_kw = round(base_kw * 1.55, 2)

            # Anomaly 2: Lighting Panel draws 5.2 kW at 02:30 AM (normally ~0.8 kW)
            if is_in_last_24h and panel == "Lighting Panel":
                if ts.hour == 2 and ts.minute == 30:
                    base_kw = 5.20
                elif ts.hour == 2 and ts.minute in (15, 45):
                    base_kw = 4.80

            active_power_kw = round(base_kw, 2)

            # Reactive Power (kVAR): Q = sqrt(S^2 - P^2) = P * sqrt((1/PF^2) - 1)
            reactive_kvar = round(
                float(active_power_kw * np.sqrt(max(0.0, (1.0 / (pf**2)) - 1.0))), 2
            )

            # Current (Amperes): I = (P(kW) * 1000) / (V * PF)
            current_a = round((active_power_kw * 1000.0) / (voltage_v * pf), 2)

            records.append({
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "panel_name": panel,
                "voltage_v": voltage_v,
                "current_a": current_a,
                "active_power_kw": active_power_kw,
                "reactive_power_kvar": reactive_kvar,
                "power_factor": pf,
            })

    df = pd.DataFrame(records)
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Generate 7-day realistic energy consumption dataset for EnergySense AI."
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=str(DATA_PATH),
        help="Path to save energy_data.csv",
    )
    args = parser.parse_args()

    out_path = Path(args.output).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating 7-day energy dataset at 15-minute frequency...")
    df = generate_energy_dataset()
    df.to_csv(out_path, index=False)

    print(f"Dataset successfully created at: {out_path}")
    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print("\nSample records:")
    print(df.head(6))


if __name__ == "__main__":
    main()
