from grid_intelligence.models import GridAnomaly

class AnomalyService:
    @staticmethod
    def get_unresolved_anomalies(severity=None, limit=10):
        qs = GridAnomaly.objects.select_related('district').filter(is_resolved=False)
        if severity:
            qs = qs.filter(severity=severity.upper())
        return qs[:limit]

    @staticmethod
    def resolve_anomaly(anomaly_id):
        return GridAnomaly.objects.filter(id=anomaly_id).update(is_resolved=True)
