from django.db import models

class District(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="District Name")
    city_hub = models.CharField(max_length=100, verbose_name="City / Economic Hub")
    discom_zone = models.CharField(max_length=20, verbose_name="DISCOM Zone") # UGVCL, DGVCL, MGVCL, PGVCL
    latitude = models.FloatField(verbose_name="Latitude")
    longitude = models.FloatField(verbose_name="Longitude")
    baseline_mw = models.FloatField(default=1000.0, verbose_name="Nominal Baseline (MW)")
    dominant_industry = models.CharField(max_length=255, blank=True, verbose_name="Dominant Industry / Character")

    class Meta:
        ordering = ['name']
        verbose_name = "Gujarat District Hub"
        verbose_name_plural = "Gujarat District Hubs"

    def __str__(self):
        return f"{self.name} ({self.city_hub}) - {self.discom_zone}"

class TelemetryRecord(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='telemetry')
    timestamp = models.DateTimeField(db_index=True)
    demand_mw = models.FloatField(verbose_name="Active Demand (MW)")
    renewable_mw = models.FloatField(default=0.0, verbose_name="Renewable Generation (MW)")
    grid_frequency_hz = models.FloatField(default=50.00, verbose_name="Grid Frequency (Hz)")
    power_factor = models.FloatField(default=0.98, verbose_name="Power Factor")
    thd_pct = models.FloatField(default=3.0, verbose_name="Total Harmonic Distortion (THD %)")

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['district', 'timestamp']),
        ]
        verbose_name = "SCADA Telemetry Record"
        verbose_name_plural = "SCADA Telemetry Records"

    @property
    def net_demand_mw(self):
        return max(0.0, self.demand_mw - self.renewable_mw)

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.district.name}: {self.demand_mw} MW"

class GridAnomaly(models.Model):
    SEVERITY_CHOICES = [
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('WARNING', 'Warning'),
        ('NORMAL', 'Normal'),
    ]

    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='anomalies')
    timestamp = models.DateTimeField(db_index=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='WARNING')
    root_cause = models.CharField(max_length=255, verbose_name="Root Cause Attribution")
    deviation_pct = models.FloatField(verbose_name="Deviation (%)")
    actual_load_mw = models.FloatField(verbose_name="Actual Load (MW)")
    expected_load_mw = models.FloatField(verbose_name="Expected Load (MW)")
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Grid Anomaly"
        verbose_name_plural = "Grid Anomalies"

    def __str__(self):
        return f"[{self.severity}] {self.district.name} - {self.root_cause} (+{self.deviation_pct:.1f}%)"

class DispatchDirective(models.Model):
    PRIORITY_CHOICES = [
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('OPTIMAL', 'Optimal'),
    ]

    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True, related_name='directives')
    created_at = models.DateTimeField(auto_now_add=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    title = models.CharField(max_length=255)
    action = models.TextField(verbose_name="Dispatch Action")
    impact = models.CharField(max_length=255, verbose_name="Expected Grid Impact")
    is_acknowledged = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "SLDC Dispatch Directive"
        verbose_name_plural = "SLDC Dispatch Directives"

    def __str__(self):
        return f"[{self.priority}] {self.title}"

class ForecastRecord(models.Model):
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True, related_name='forecasts')
    generated_at = models.DateTimeField(auto_now_add=True)
    forecast_timestamp = models.DateTimeField()
    hours_ahead = models.CharField(max_length=10) # +1h, +2h, etc.
    predicted_load_mw = models.FloatField()
    gbm_load_mw = models.FloatField(null=True, blank=True)
    threshold_mw = models.FloatField(default=21500.0)
    peak_alert = models.BooleanField(default=False)

    class Meta:
        ordering = ['forecast_timestamp']
        verbose_name = "Demand Forecast"
        verbose_name_plural = "Demand Forecasts"

    def __str__(self):
        return f"[{self.hours_ahead}] {self.predicted_load_mw} MW (Peak: {self.peak_alert})"
