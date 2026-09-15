import json
from django.shortcuts import render
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import District, TelemetryRecord, GridAnomaly, DispatchDirective, ForecastRecord
from .serializers import (
    DistrictSerializer, TelemetryRecordSerializer, GridAnomalySerializer,
    DispatchDirectiveSerializer, ForecastRecordSerializer
)
from .services.telemetry_service import TelemetryService
from .services.copilot_service import CopilotService

class DashboardView(TemplateView):
    template_name = "grid_intelligence/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        summary = TelemetryService.get_latest_state_summary()
        
        districts = District.objects.all()
        latest_readings = []
        latest_time = summary["timestamp"] if summary else None

        for d in districts:
            t = d.telemetry.filter(timestamp=latest_time).first() if latest_time else None
            if t:
                latest_readings.append({
                    "id": d.id,
                    "name": d.name,
                    "city": d.city_hub,
                    "discom": d.discom_zone,
                    "lat": d.latitude,
                    "lon": d.longitude,
                    "demand_mw": round(t.demand_mw, 1),
                    "renewable_mw": round(t.renewable_mw, 1),
                    "frequency": round(t.grid_frequency_hz, 3),
                    "pf": round(t.power_factor, 2),
                    "thd": round(t.thd_pct, 1),
                    "industry": d.dominant_industry
                })
                
        leaderboard = sorted(latest_readings, key=lambda x: x["demand_mw"], reverse=True)
        anomalies = GridAnomaly.objects.select_related('district').filter(is_resolved=False)[:8]
        directives = DispatchDirective.objects.select_related('district').all()[:6]
        forecasts = ForecastRecord.objects.all()[:4]

        ctx.update({
            "latest_timestamp": latest_time,
            "total_state_demand_mw": summary["total_demand_mw"] if summary else 0.0,
            "total_renewable_mw": summary["total_renewable_mw"] if summary else 0.0,
            "renewable_share_pct": summary["renewable_share_pct"] if summary else 0.0,
            "net_demand_mw": summary["net_demand_mw"] if summary else 0.0,
            "avg_frequency_hz": summary["average_frequency_hz"] if summary else 50.0,
            "avg_power_factor": summary["average_power_factor"] if summary else 0.98,
            "avg_thd_pct": summary["average_thd_pct"] if summary else 3.0,
            "dsm_exposure_lakhs": summary["dsm_penalty_lakhs"] if summary else 0.0,
            "avoided_co2_hr": round((summary["total_renewable_mw"] if summary else 0.0) * 0.82, 1),
            "districts_json": json.dumps(latest_readings),
            "leaderboard": leaderboard,
            "anomalies": anomalies,
            "directives": directives,
            "forecasts": forecasts,
        })
        return ctx

class SwaggerDocsView(TemplateView):
    template_name = "grid_intelligence/swagger_docs.html"

# ----------------- REST API VIEWS -----------------

class APIRootView(APIView):
    """GET /api/v1/ - API Index & Documentation Explorer"""
    def get(self, request):
        return Response({
            "service": "G-EnergySense AI Enterprise REST API",
            "version": "1.0.0",
            "documentation": "/api/docs/",
            "endpoints": {
                "live_grid": "/api/v1/grid/live/",
                "districts": "/api/v1/districts/",
                "anomalies": "/api/v1/anomalies/",
                "forecast": "/api/v1/forecast/",
                "directives": "/api/v1/directives/",
                "copilot_chat": "/api/v1/copilot/chat/"
            }
        })

class LiveGridSummaryAPIView(APIView):
    def get(self, request):
        summary = TelemetryService.get_latest_state_summary()
        if not summary:
            return Response({"status": "error", "message": "No telemetry data found"}, status=status.HTTP_404_NOT_FOUND)

        district_data = []
        for r in summary["records"]:
            district_data.append({
                "district": r.district.name,
                "city": r.district.city_hub,
                "discom": r.district.discom_zone,
                "demand_mw": r.demand_mw,
                "renewable_mw": r.renewable_mw,
                "net_demand_mw": r.net_demand_mw,
                "frequency_hz": r.grid_frequency_hz,
                "power_factor": r.power_factor,
                "thd_pct": r.thd_pct
            })
            
        return Response({
            "status": "success",
            "timestamp": str(summary["timestamp"]),
            "state_total_demand_mw": summary["total_demand_mw"],
            "state_renewable_mw": summary["total_renewable_mw"],
            "state_net_demand_mw": summary["net_demand_mw"],
            "renewable_share_pct": summary["renewable_share_pct"],
            "grid_frequency_hz": summary["average_frequency_hz"],
            "districts": district_data
        })

class DistrictListAPIView(APIView):
    def get(self, request):
        districts = District.objects.all()
        serializer = DistrictSerializer(districts, many=True)
        return Response({"status": "success", "count": len(serializer.data), "districts": serializer.data})

class AnomalyListAPIView(APIView):
    def get(self, request):
        severity = request.query_params.get('severity')
        qs = GridAnomaly.objects.select_related('district').all()
        if severity:
            qs = qs.filter(severity=severity.upper())
        qs = qs[:15]
        serializer = GridAnomalySerializer(qs, many=True)
        return Response({"status": "success", "count": len(serializer.data), "anomalies": serializer.data})

class ForecastAPIView(APIView):
    def get(self, request):
        qs = ForecastRecord.objects.all()[:6]
        serializer = ForecastRecordSerializer(qs, many=True)
        return Response({"status": "success", "forecast": serializer.data})

class DirectiveListAPIView(APIView):
    def get(self, request):
        qs = DispatchDirective.objects.select_related('district').all()[:10]
        serializer = DispatchDirectiveSerializer(qs, many=True)
        return Response({"status": "success", "directives": serializer.data})

class CopilotChatAPIView(APIView):
    def post(self, request):
        query = request.data.get("query", "").strip()
        if not query:
            return Response({"error": "Query string is required."}, status=status.HTTP_400_BAD_REQUEST)

        reply, markdown_brief = CopilotService.process_operator_query(query)

        return Response({
            "status": "success",
            "query": query,
            "response": reply,
            "markdown_brief": markdown_brief
        })
