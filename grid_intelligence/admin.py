from django.contrib import admin
from .models import District, TelemetryRecord, GridAnomaly, DispatchDirective, ForecastRecord

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'city_hub', 'discom_zone', 'baseline_mw', 'latitude', 'longitude')
    list_filter = ('discom_zone',)
    search_fields = ('name', 'city_hub', 'dominant_industry')

@admin.register(TelemetryRecord)
class TelemetryRecordAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'district', 'demand_mw', 'renewable_mw', 'grid_frequency_hz', 'power_factor', 'thd_pct')
    list_filter = ('district__discom_zone', 'district')
    date_hierarchy = 'timestamp'
    search_fields = ('district__name',)

@admin.register(GridAnomaly)
class GridAnomalyAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'district', 'severity', 'root_cause', 'deviation_pct', 'actual_load_mw', 'is_resolved')
    list_filter = ('severity', 'is_resolved', 'district__discom_zone')
    search_fields = ('district__name', 'root_cause')

@admin.register(DispatchDirective)
class DispatchDirectiveAdmin(admin.ModelAdmin):
    list_display = ('priority', 'title', 'district', 'created_at', 'is_acknowledged')
    list_filter = ('priority', 'is_acknowledged')
    search_fields = ('title', 'action', 'impact')

@admin.register(ForecastRecord)
class ForecastRecordAdmin(admin.ModelAdmin):
    list_display = ('forecast_timestamp', 'hours_ahead', 'district', 'predicted_load_mw', 'threshold_mw', 'peak_alert')
    list_filter = ('peak_alert',)
