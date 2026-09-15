from rest_framework import serializers
from .models import District, TelemetryRecord, GridAnomaly, DispatchDirective, ForecastRecord

class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = '__all__'

class TelemetryRecordSerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source='district.name', read_only=True)
    city_hub = serializers.CharField(source='district.city_hub', read_only=True)
    discom_zone = serializers.CharField(source='district.discom_zone', read_only=True)
    net_demand_mw = serializers.FloatField(read_only=True)

    class Meta:
        model = TelemetryRecord
        fields = [
            'id', 'district', 'district_name', 'city_hub', 'discom_zone',
            'timestamp', 'demand_mw', 'renewable_mw', 'net_demand_mw',
            'grid_frequency_hz', 'power_factor', 'thd_pct'
        ]

class GridAnomalySerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source='district.name', read_only=True)
    city_hub = serializers.CharField(source='district.city_hub', read_only=True)

    class Meta:
        model = GridAnomaly
        fields = '__all__'

class DispatchDirectiveSerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source='district.name', read_only=True, default='Statewide')

    class Meta:
        model = DispatchDirective
        fields = '__all__'

class ForecastRecordSerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source='district.name', read_only=True, default='All Gujarat (Statewide)')

    class Meta:
        model = ForecastRecord
        fields = '__all__'
