import os
from datetime import datetime
from pathlib import Path
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction

from grid_intelligence.models import District, TelemetryRecord, GridAnomaly, DispatchDirective, ForecastRecord

class Command(BaseCommand):
    help = 'Seeds Gujarat 10 Districts, SCADA telemetry, anomalies, forecasts, and SLDC directives from dataset'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting Gujarat State Grid Database Seeding..."))
        
        csv_path = Path(__file__).resolve().parents[3] / "src" / "data" / "gujarat_grid_data.csv"
        src_dir = Path(__file__).resolve().parents[3] / "src"
        import sys
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))

        if not csv_path.exists():
            self.stdout.write(self.style.WARNING("Dataset not found at src/data/gujarat_grid_data.csv. Generating now..."))
            from data.generate_gujarat_data import generate_gujarat_grid_dataset
            df = generate_gujarat_grid_dataset(str(csv_path))
        else:
            df = pd.read_csv(csv_path)
            
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        HUBS = {
            "Ahmedabad": {"city": "Ahmedabad Metro", "discom": "UGVCL", "lat": 23.0225, "lon": 72.5714, "base": 3600.0, "ind": "Urban Commercial, Metro Rail & IT"},
            "Surat": {"city": "Surat City", "discom": "DGVCL", "lat": 21.1702, "lon": 72.8311, "base": 4200.0, "ind": "Textile Weaving & Diamond Polishing Hub"},
            "Vadodara": {"city": "Vadodara City", "discom": "MGVCL", "lat": 22.3072, "lon": 73.1812, "base": 2400.0, "ind": "Heavy Engineering, Petrochemicals & SLDC"},
            "Rajkot": {"city": "Rajkot City", "discom": "PGVCL", "lat": 22.3039, "lon": 70.8022, "base": 2100.0, "ind": "Automotive Casting & Induction Melting"},
            "Anand & Kheda": {"city": "Anand / Changa", "discom": "MGVCL", "lat": 22.5645, "lon": 72.9289, "base": 1400.0, "ind": "Amul Dairy, Agro Processing & CHARUSAT Zone"},
            "Gandhinagar": {"city": "Gandhinagar / GIFT City", "discom": "UGVCL", "lat": 23.2156, "lon": 72.6369, "base": 1100.0, "ind": "International Fintech & Hyperscale Data Centers"},
            "Kutch": {"city": "Bhuj / Mundra", "discom": "PGVCL", "lat": 23.2420, "lon": 69.6669, "base": 2800.0, "ind": "Mundra Mega Port & Khavda Renewable Park"},
            "Bharuch": {"city": "Bharuch / Dahej", "discom": "DGVCL", "lat": 21.7051, "lon": 72.9959, "base": 2600.0, "ind": "Dahej PCPIR & Bulk Specialty Chemicals"},
            "Jamnagar": {"city": "Jamnagar City", "discom": "PGVCL", "lat": 22.4707, "lon": 70.0577, "base": 2300.0, "ind": "Petroleum Refining & Brass Component Units"},
            "Bhavnagar": {"city": "Bhavnagar / Alang", "discom": "PGVCL", "lat": 21.7645, "lon": 72.1519, "base": 1200.0, "ind": "Alang Shipbreaking & Steel Re-Rolling Mills"}
        }
        
        district_objects = {}
        for d_name, info in HUBS.items():
            dist_obj, created = District.objects.update_or_create(
                name=d_name,
                defaults={
                    "city_hub": info["city"],
                    "discom_zone": info["discom"],
                    "latitude": info["lat"],
                    "longitude": info["lon"],
                    "baseline_mw": info["base"],
                    "dominant_industry": info["ind"]
                }
            )
            district_objects[d_name] = dist_obj
            
        self.stdout.write(self.style.SUCCESS(f"Configured {len(district_objects)} Gujarat District Hubs."))
        
        existing_telemetry_count = TelemetryRecord.objects.count()
        if existing_telemetry_count < 1000:
            self.stdout.write("Populating Telemetry Records (6,700+ rows)...")
            records_to_create = []
            for _, r in df.iterrows():
                d_name = r.get("district")
                if d_name in district_objects:
                    records_to_create.append(TelemetryRecord(
                        district=district_objects[d_name],
                        timestamp=r["timestamp"],
                        demand_mw=float(r["demand_mw"]),
                        renewable_mw=float(r.get("renewable_mw", 0.0)),
                        grid_frequency_hz=float(r.get("grid_frequency_hz", 50.0)),
                        power_factor=float(r.get("power_factor", 0.98)),
                        thd_pct=float(r.get("thd_pct", 3.0))
                    ))
                    
            with transaction.atomic():
                TelemetryRecord.objects.bulk_create(records_to_create, batch_size=2000)
            self.stdout.write(self.style.SUCCESS(f"Created {len(records_to_create)} Telemetry Records."))
        else:
            self.stdout.write(self.style.NOTICE(f"Found {existing_telemetry_count} existing Telemetry Records. Skipping bulk create."))

        GridAnomaly.objects.all().delete()
        if str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))
        from anomaly import detect_anomalies
        scored = detect_anomalies(df)
        anom_rows = scored[scored["is_anomaly"]].sort_values("timestamp", ascending=False).head(30)
        
        anom_to_create = []
        for _, a in anom_rows.iterrows():
            d_name = a.get("district")
            if d_name in district_objects:
                anom_to_create.append(GridAnomaly(
                    district=district_objects[d_name],
                    timestamp=a["timestamp"],
                    severity=a.get("severity", "WARNING"),
                    root_cause=a.get("root_cause", "Unscheduled Feeder Draw"),
                    deviation_pct=float(a.get("deviation_pct", 0.0)),
                    actual_load_mw=float(a.get("demand_mw", 0.0)),
                    expected_load_mw=float(a.get("expected_load", 0.0)),
                    is_resolved=False
                ))
        GridAnomaly.objects.bulk_create(anom_to_create)
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(anom_to_create)} Grid Anomalies."))

        DispatchDirective.objects.all().delete()
        from recommendations import generate_recommendations
        recs = generate_recommendations(anom_rows.head(5))
        for r in recs:
            p_name = r.get("panel", "")
            d_obj = district_objects.get(p_name, None)
            DispatchDirective.objects.create(
                district=d_obj,
                priority=r.get("priority", "MEDIUM"),
                title=r.get("title", "Grid Action Directive"),
                action=r.get("action", ""),
                impact=r.get("impact", "")
            )
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(recs)} Dispatch Directives."))

        ForecastRecord.objects.all().delete()
        from forecasting import forecast_next_hours
        fc = forecast_next_hours(hours_ahead=4, df=df)
        for _, f_row in fc.iterrows():
            ForecastRecord.objects.create(
                district=None,
                forecast_timestamp=f_row["timestamp"],
                hours_ahead=f_row["hours_ahead"],
                predicted_load_mw=float(f_row["predicted_load_mw"]),
                gbm_load_mw=float(f_row.get("gbm_load_mw", f_row["predicted_load_mw"])),
                threshold_mw=float(f_row["threshold_mw"]),
                peak_alert=bool(f_row["peak_alert"])
            )
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(fc)} Forecast Records."))

        self.stdout.write(self.style.SUCCESS("Database Seeding Completed Successfully!"))
