from django.contrib import admin
from django.utils.html import format_html
from .models import District, TelemetryRecord, GridAnomaly, DispatchDirective, ForecastRecord

# Enterprise Admin Site Customization
admin.site.site_header = "⚡ Gujarat State Load Despatch Centre (SLDC) — G-EnergySense AI"
admin.site.site_title = "SLDC Grid Command Admin"
admin.site.index_title = "SCADA Telemetry & Regional Feeder Administration"

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'city_hub', 'discom_badge', 'baseline_mw', 'coordinates', 'dominant_industry')
    list_filter = ('discom_zone',)
    search_fields = ('name', 'city_hub', 'dominant_industry')
    ordering = ('name',)

    def discom_badge(self, obj):
        colors = {
            'UGVCL': '#3b82f6',
            'DGVCL': '#f59e0b',
            'MGVCL': '#10b981',
            'PGVCL': '#8b5cf6'
        }
        color = colors.get(obj.discom_zone, '#64748b')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color, obj.discom_zone
        )
    discom_badge.short_description = "DISCOM"

    def coordinates(self, obj):
        return f"{obj.latitude:.2f}° N, {obj.longitude:.2f}° E"
    coordinates.short_description = "GPS Coordinates"


@admin.register(TelemetryRecord)
class TelemetryRecordAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'district', 'demand_mw', 'renewable_mw', 'frequency_status', 'power_factor_status', 'thd_status')
    list_filter = ('district__discom_zone', 'district')
    date_hierarchy = 'timestamp'
    search_fields = ('district__name',)
    list_per_page = 50

    def frequency_status(self, obj):
        if obj.grid_frequency_hz < 49.95:
            return format_html('<span style="color: #ef4444; font-weight: bold;">⚠️ {} Hz (SAG)</span>', obj.grid_frequency_hz)
        return format_html('<span style="color: #10b981; font-weight: bold;">{} Hz</span>', obj.grid_frequency_hz)
    frequency_status.short_description = "Frequency"

    def power_factor_status(self, obj):
        if obj.power_factor < 0.95:
            return format_html('<span style="color: #f59e0b; font-weight: bold;">{} (Low)</span>', obj.power_factor)
        return format_html('<span style="color: #10b981;">{}</span>', obj.power_factor)
    power_factor_status.short_description = "PF"

    def thd_status(self, obj):
        if obj.thd_pct > 5.0:
            return format_html('<span style="color: #ef4444; font-weight: bold;">⚠️ {}% (Breach)</span>', obj.thd_pct)
        return format_html('<span style="color: #64748b;">{}%</span>', obj.thd_pct)
    thd_status.short_description = "IEEE 519 THD"


@admin.register(GridAnomaly)
class GridAnomalyAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'district', 'severity_badge', 'root_cause', 'deviation_pct', 'actual_load_mw', 'resolved_status')
    list_filter = ('severity', 'is_resolved', 'district__discom_zone')
    search_fields = ('district__name', 'root_cause')
    actions = ['mark_as_resolved', 'mark_as_unresolved']

    def severity_badge(self, obj):
        colors = {
            'CRITICAL': '#ef4444',
            'HIGH': '#f59e0b',
            'WARNING': '#eab308',
            'NORMAL': '#10b981'
        }
        color = colors.get(obj.severity, '#64748b')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color, obj.severity
        )
    severity_badge.short_description = "Severity"

    def resolved_status(self, obj):
        if obj.is_resolved:
            return format_html('<span style="color: #10b981; font-weight: bold;">✓ Resolved</span>')
        return format_html('<span style="color: #ef4444; font-weight: bold;">● Active</span>')
    resolved_status.short_description = "Status"

    @admin.action(description="Mark selected anomalies as Resolved")
    def mark_as_resolved(self, request, queryset):
        queryset.update(is_resolved=True)

    @admin.action(description="Mark selected anomalies as Active (Unresolved)")
    def mark_as_unresolved(self, request, queryset):
        queryset.update(is_resolved=False)


@admin.register(DispatchDirective)
class DispatchDirectiveAdmin(admin.ModelAdmin):
    list_display = ('priority_badge', 'title', 'district', 'created_at', 'ack_status')
    list_filter = ('priority', 'is_acknowledged')
    search_fields = ('title', 'action', 'impact')
    actions = ['acknowledge_directives']

    def priority_badge(self, obj):
        colors = {
            'CRITICAL': '#ef4444',
            'HIGH': '#f59e0b',
            'MEDIUM': '#3b82f6',
            'OPTIMAL': '#10b981'
        }
        color = colors.get(obj.priority, '#64748b')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color, obj.priority
        )
    priority_badge.short_description = "Priority"

    def ack_status(self, obj):
        if obj.is_acknowledged:
            return format_html('<span style="color: #10b981;">✓ Acknowledged</span>')
        return format_html('<span style="color: #f59e0b; font-weight: bold;">Pending Action</span>')
    ack_status.short_description = "SLDC Status"

    @admin.action(description="Acknowledge selected dispatch directives")
    def acknowledge_directives(self, request, queryset):
        queryset.update(is_acknowledged=True)


@admin.register(ForecastRecord)
class ForecastRecordAdmin(admin.ModelAdmin):
    list_display = ('forecast_timestamp', 'hours_ahead', 'district_label', 'predicted_load_mw', 'threshold_mw', 'alert_badge')
    list_filter = ('peak_alert',)

    def district_label(self, obj):
        return obj.district.name if obj.district else "All Gujarat (Statewide)"
    district_label.short_description = "Scope"

    def alert_badge(self, obj):
        if obj.peak_alert:
            return format_html('<span style="background-color: #ef4444; color: white; padding: 2px 6px; border-radius: 3px; font-weight: bold; font-size: 10px;">⚠️ PEAK BREACH</span>')
        return format_html('<span style="background-color: #10b981; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">🟢 NOMINAL</span>')
    alert_badge.short_description = "Alert Status"
