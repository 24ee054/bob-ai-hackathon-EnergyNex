from datetime import datetime
from django.db.models import Avg, Sum, Max
from grid_intelligence.models import District, TelemetryRecord

class TelemetryService:
    @staticmethod
    def get_latest_state_summary():
        latest_time = TelemetryRecord.objects.order_by('-timestamp').values_list('timestamp', flat=True).first()
        if not latest_time:
            return None
            
        records = TelemetryRecord.objects.filter(timestamp=latest_time).select_related('district')
        total_mw = sum(r.demand_mw for r in records)
        total_ren = sum(r.renewable_mw for r in records)
        avg_freq = sum(r.grid_frequency_hz for r in records) / len(records) if records else 50.0
        avg_pf = sum(r.power_factor for r in records) / len(records) if records else 0.98
        avg_thd = sum(r.thd_pct for r in records) / len(records) if records else 3.0

        dsm_exposure = 0.0
        if avg_freq < 49.95:
            dsm_exposure = round((total_mw * 0.04) * (50.0 - avg_freq) * 450, 2)

        return {
            "timestamp": latest_time,
            "total_demand_mw": round(total_mw, 1),
            "total_renewable_mw": round(total_ren, 1),
            "net_demand_mw": round(max(0.0, total_mw - total_ren), 1),
            "renewable_share_pct": round((total_ren / max(total_mw, 1.0)) * 100.0, 1),
            "average_frequency_hz": round(avg_freq, 3),
            "average_power_factor": round(avg_pf, 3),
            "average_thd_pct": round(avg_thd, 2),
            "dsm_penalty_lakhs": dsm_exposure,
            "records": records
        }
