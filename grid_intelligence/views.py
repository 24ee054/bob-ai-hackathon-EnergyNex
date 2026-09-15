import json
from datetime import datetime, timedelta
from pathlib import Path
from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import District, TelemetryRecord, GridAnomaly, DispatchDirective, ForecastRecord
from .serializers import (
    DistrictSerializer, TelemetryRecordSerializer, GridAnomalySerializer,
    DispatchDirectiveSerializer, ForecastRecordSerializer
)

class DashboardView(TemplateView):
    template_name = "grid_intelligence/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        latest_time = TelemetryRecord.objects.order_by('-timestamp').values_list('timestamp', flat=True).first()
        
        districts = District.objects.all()
        latest_readings = []
        total_mw = 0.0
        total_ren = 0.0
        freq_list = []
        pf_list = []
        thd_list = []
        
        for d in districts:
            t = d.telemetry.filter(timestamp=latest_time).first() if latest_time else None
            if t:
                total_mw += t.demand_mw
                total_ren += t.renewable_mw
                freq_list.append(t.grid_frequency_hz)
                pf_list.append(t.power_factor)
                thd_list.append(t.thd_pct)
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
        
        avg_freq = sum(freq_list)/len(freq_list) if freq_list else 50.00
        avg_pf = sum(pf_list)/len(pf_list) if pf_list else 0.98
        avg_thd = sum(thd_list)/len(thd_list) if thd_list else 3.2
        ren_pct = round((total_ren / max(total_mw, 1.0)) * 100.0, 1)

        anomalies = GridAnomaly.objects.select_related('district').filter(is_resolved=False)[:8]
        directives = DispatchDirective.objects.select_related('district').all()[:6]
        forecasts = ForecastRecord.objects.all()[:4]

        dsm_exposure = 0.0
        if avg_freq < 49.95:
            dsm_exposure = round((total_mw * 0.04) * (50.0 - avg_freq) * 450, 2)

        ctx.update({
            "latest_timestamp": latest_time,
            "total_state_demand_mw": round(total_mw, 1),
            "total_renewable_mw": round(total_ren, 1),
            "renewable_share_pct": ren_pct,
            "net_demand_mw": round(max(0.0, total_mw - total_ren), 1),
            "avg_frequency_hz": round(avg_freq, 3),
            "avg_power_factor": round(avg_pf, 3),
            "avg_thd_pct": round(avg_thd, 2),
            "dsm_exposure_lakhs": dsm_exposure,
            "avoided_co2_hr": round(total_ren * 0.82, 1),
            "districts_json": json.dumps(latest_readings),
            "leaderboard": leaderboard,
            "anomalies": anomalies,
            "directives": directives,
            "forecasts": forecasts,
        })
        return ctx

class LiveGridSummaryAPIView(APIView):
    def get(self, request):
        latest_time = TelemetryRecord.objects.order_by('-timestamp').values_list('timestamp', flat=True).first()
        records = TelemetryRecord.objects.filter(timestamp=latest_time).select_related('district')
        
        total_mw = sum(r.demand_mw for r in records)
        total_ren = sum(r.renewable_mw for r in records)
        avg_freq = sum(r.grid_frequency_hz for r in records) / len(records) if records else 50.0
        
        district_data = []
        for r in records:
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
            "timestamp": str(latest_time),
            "state_total_demand_mw": round(total_mw, 1),
            "state_renewable_mw": round(total_ren, 1),
            "state_net_demand_mw": round(max(0.0, total_mw - total_ren), 1),
            "renewable_share_pct": round((total_ren / max(total_mw, 1)) * 100, 1),
            "grid_frequency_hz": round(avg_freq, 3),
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

        q_lower = query.lower()
        latest_time = TelemetryRecord.objects.order_by('-timestamp').values_list('timestamp', flat=True).first()
        records = TelemetryRecord.objects.filter(timestamp=latest_time).select_related('district')
        total_mw = sum(r.demand_mw for r in records)
        total_ren = sum(r.renewable_mw for r in records)
        avg_freq = sum(r.grid_frequency_hz for r in records) / len(records) if records else 50.0

        markdown_brief = None

        if "brief" in q_lower or "report" in q_lower or "incident" in q_lower:
            anoms = GridAnomaly.objects.filter(is_resolved=False)[:4]
            dirs = DispatchDirective.objects.all()[:3]
            fc = ForecastRecord.objects.all()[:4]

            lines = [
                "# ⚡ SLDC Executive Operational Intelligence Brief",
                f"**Timestamp:** `{latest_time}` | **Agent:** IBM Bob Autonomous Grid Copilot",
                f"**State Active Demand:** `{total_mw:,.0f} MW` | **Frequency:** `{avg_freq:.3f} Hz` | **Renewable:** `{total_ren:,.0f} MW`\n",
                "## 1. Regional Feeder Status",
            ]
            for r in list(records)[:5]:
                lines.append(f"- **{r.district.name} ({r.district.city_hub})**: `{r.demand_mw:,.0f} MW` (PF: `{r.power_factor:.2f}`, THD: `{r.thd_pct:.1f}%`)")
            
            lines.append("\n## 2. Active Anomalies")
            for a in anoms:
                lines.append(f"- **[{a.severity}] {a.district.name}**: {a.root_cause} (+{a.deviation_pct:.1f}% surge over expected {a.expected_load_mw:,.0f} MW)")
            
            lines.append("\n## 3. Forward Peak Projections (Next 4h)")
            for f in fc:
                lines.append(f"- `{f.hours_ahead}`: `{f.predicted_load_mw:,.0f} MW` ({'⚠️ PEAK ALERT' if f.peak_alert else '🟢 Nominal'})")

            lines.append("\n## 4. Dispatched Control Directives")
            for d in dirs:
                lines.append(f"- **[{d.priority}] {d.title}**\n  👉 Action: {d.action}\n  📈 Impact: {d.impact}")

            markdown_brief = "\n".join(lines)
            reply = f"I have compiled the complete SLDC Executive Incident Brief for the Gujarat State Grid at timestamp {latest_time}. Total active draw is {total_mw:,.0f} MW with frequency at {avg_freq:.3f} Hz. You can review the breakdown or download the executive markdown brief."

        elif "anand" in q_lower or "kheda" in q_lower or "charusat" in q_lower:
            d = District.objects.filter(name__icontains="Anand").first()
            if d:
                t = d.telemetry.filter(timestamp=latest_time).first()
                anom = d.anomalies.filter(is_resolved=False).first()
                reply = (
                    f"📍 **Anand & Kheda (CHARUSAT Zone) Telemetry Audit:**\n"
                    f"• DISCOM: **MGVCL**\n"
                    f"• Current Active Draw: **{t.demand_mw:,.1f} MW** (Nominal Baseline: {d.baseline_mw:,.0f} MW)\n"
                    f"• Grid Frequency: **{t.grid_frequency_hz:.3f} Hz** | Power Factor: **{t.power_factor:.2f}** | THD: **{t.thd_pct:.1f}%**\n"
                    f"• Status: {'⚠️ Anomaly flagged: ' + anom.root_cause if anom else '🟢 Normal operation across agro and university campus feeders.'}\n"
                    f"• Action: 66kV Changa & Mogar substations operating within safe transformer temperature limits."
                )
            else:
                reply = "Anand & Kheda district record could not be found."

        elif "surat" in q_lower or "textile" in q_lower:
            d = District.objects.filter(name__icontains="Surat").first()
            if d:
                t = d.telemetry.filter(timestamp=latest_time).first()
                reply = (
                    f"📍 **Surat Industrial Corridor Audit (DGVCL):**\n"
                    f"• Current Active Demand: **{t.demand_mw:,.1f} MW**\n"
                    f"• Total Harmonic Distortion: **{t.thd_pct:.1f}%** (IEEE 519 limit: 5.0%)\n"
                    f"• Action: Enforce staggered shift timings in Pandesara & Sachin GIDC textile clusters to prevent local 220kV bus overheating."
                )
        elif "solar" in q_lower or "duck" in q_lower or "ramp" in q_lower:
            reply = (
                f"🦆 **Gujarat Solar Ramp & Duck Curve Analysis:**\n"
                f"• Current Renewable Generation: **{total_ren:,.1f} MW** ({round((total_ren/max(total_mw,1))*100, 1)}% of state demand)\n"
                f"• Sunset Ramp-Down Rate: Estimated **~1,240 MW/hour** transition.\n"
                f"• Directive: Kadana & Sardar Sarovar hydro generation synchronized for evening peak substitution."
            )
        else:
            reply = (
                f"🤖 **IBM Bob Grid Copilot:** I am continuously monitoring all 10 Gujarat districts. "
                f"Current statewide load is **{total_mw:,.0f} MW** with grid frequency at **{avg_freq:.3f} Hz**. "
                f"You can ask me to audit specific districts (e.g., Anand / CHARUSAT zone, Surat), analyze the duck curve, or generate an SLDC Executive Incident Brief."
            )

        return Response({
            "status": "success",
            "query": query,
            "response": reply,
            "markdown_brief": markdown_brief
        })
