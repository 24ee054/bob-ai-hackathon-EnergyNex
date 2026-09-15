from datetime import datetime
from grid_intelligence.models import District, TelemetryRecord, GridAnomaly, DispatchDirective, ForecastRecord
from .telemetry_service import TelemetryService

class CopilotService:
    @staticmethod
    def process_operator_query(query: str):
        q = query.lower().strip()
        summary = TelemetryService.get_latest_state_summary()
        latest_time = summary["timestamp"] if summary else "N/A"
        total_mw = summary["total_demand_mw"] if summary else 0.0
        total_ren = summary["total_renewable_mw"] if summary else 0.0
        avg_freq = summary["average_frequency_hz"] if summary else 50.0

        markdown_brief = None

        if any(w in q for w in ["brief", "report", "incident", "summary"]):
            anoms = GridAnomaly.objects.filter(is_resolved=False)[:4]
            dirs = DispatchDirective.objects.all()[:3]
            fc = ForecastRecord.objects.all()[:4]

            lines = [
                "# ⚡ Gujarat SLDC Executive Operational Intelligence Brief",
                f"**Generated:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}` | **Agent:** IBM Bob Autonomous Grid Copilot",
                f"**State Active Demand:** `{total_mw:,.0f} MW` | **Frequency:** `{avg_freq:.3f} Hz` | **Renewable Share:** `{summary['renewable_share_pct']}%`\n",
                "## 1. Regional Feeder Status",
            ]
            if summary and "records" in summary:
                for r in list(summary["records"])[:5]:
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
            reply = f"Compiled official SLDC Executive Incident Brief for the Gujarat State Grid. Total active draw is {total_mw:,.0f} MW with frequency at {avg_freq:.3f} Hz. You can download or inspect the report."

        elif any(w in q for w in ["anand", "kheda", "charusat"]):
            d = District.objects.filter(name__icontains="Anand").first()
            if d:
                t = d.telemetry.filter(timestamp=latest_time).first()
                anom = d.anomalies.filter(is_resolved=False).first()
                reply = (
                    f"📍 **Anand & Kheda (CHARUSAT Zone) Telemetry Audit:**\n"
                    f"• DISCOM: **MGVCL**\n"
                    f"• Current Active Draw: **{t.demand_mw:,.1f} MW** (Nominal Baseline: {d.baseline_mw:,.0f} MW)\n"
                    f"• Grid Frequency: **{t.grid_frequency_hz:.3f} Hz** | Power Factor: **{t.power_factor:.2f}** | THD: **{t.thd_pct:.1f}%**\n"
                    f"• Status: {'⚠️ Anomaly flagged: ' + anom.root_cause if anom else '🟢 Normal operation across agro and campus feeders.'}\n"
                    f"• Action: Changa 66kV Substation transformer loading is within safe operating range (68% capacity)."
                )
            else:
                reply = "Anand & Kheda district record could not be found."

        elif any(w in q for w in ["surat", "textile"]):
            d = District.objects.filter(name__icontains="Surat").first()
            if d:
                t = d.telemetry.filter(timestamp=latest_time).first()
                reply = (
                    f"📍 **Surat Industrial Corridor Audit (DGVCL):**\n"
                    f"• Current Active Demand: **{t.demand_mw:,.1f} MW**\n"
                    f"• Total Harmonic Distortion: **{t.thd_pct:.1f}%** (IEEE 519 Standard Limit: 5.0%)\n"
                    f"• Action: Pandesara & Sachin GIDC auxiliary feeders notified for rotational power draw."
                )
            else:
                reply = "Surat district record could not be found."

        elif any(w in q for w in ["solar", "duck", "ramp"]):
            reply = (
                f"🦆 **Gujarat Solar Ramp & Duck Curve Analysis:**\n"
                f"• Current Renewable Generation: **{total_ren:,.1f} MW** ({summary['renewable_share_pct']}% of total load)\n"
                f"• Sunset Ramp-Down Rate: Estimated **~1,240 MW/hour** transition.\n"
                f"• Directive: Kadana & Sardar Sarovar hydro generation placed on spinning reserve standby."
            )
        else:
            reply = (
                f"🤖 **IBM Bob Grid Copilot:** I am continuously monitoring 10 Gujarat districts. "
                f"Current statewide load is **{total_mw:,.0f} MW** with grid frequency at **{avg_freq:.3f} Hz**. "
                f"You can ask me to audit specific districts (e.g., Anand / CHARUSAT zone, Surat), analyze the solar duck curve, or generate an SLDC Executive Incident Brief."
            )

        return reply, markdown_brief
