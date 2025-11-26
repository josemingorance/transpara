"""Analytics models for temporal analysis and historical tracking."""
from django.db import models


class HistoricalSnapshot(models.Model):
    """
    Snapshot of contract metrics at a specific point in time.

    Tracks metrics like average risk, budget totals, and contract counts
    to enable trend detection and historical analysis.
    """

    # Temporal info
    snapshot_date = models.DateField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Scope
    source_platform = models.CharField(
        max_length=50,
        choices=[
            ("BOE", "Boletín Oficial del Estado"),
            ("PCSP", "Plataforma de Contratación del Sector Público"),
            ("ALL", "All Sources"),
        ],
        default="ALL",
        db_index=True,
    )

    # Contract Statistics
    total_contracts = models.IntegerField(default=0)
    published_contracts = models.IntegerField(default=0)
    awarded_contracts = models.IntegerField(default=0)
    in_progress_contracts = models.IntegerField(default=0)
    completed_contracts = models.IntegerField(default=0)

    # Financial Data
    total_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_awarded = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    avg_budget = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    avg_awarded = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Risk Analysis
    avg_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    high_risk_count = models.IntegerField(default=0)  # Risk >= 60
    medium_risk_count = models.IntegerField(default=0)  # 40 <= Risk < 60
    low_risk_count = models.IntegerField(default=0)  # 20 <= Risk < 40

    # Contract Types
    works_count = models.IntegerField(default=0)
    services_count = models.IntegerField(default=0)
    supplies_count = models.IntegerField(default=0)
    mixed_count = models.IntegerField(default=0)
    other_count = models.IntegerField(default=0)

    # Procedure Types
    open_procedure_count = models.IntegerField(default=0)
    restricted_procedure_count = models.IntegerField(default=0)
    negotiated_procedure_count = models.IntegerField(default=0)

    # Overpricing Detection
    overpriced_count = models.IntegerField(default=0)  # Contracts flagged as overpriced
    avg_overpricing_risk = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Delay Risk
    avg_delay_risk = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    high_delay_risk_count = models.IntegerField(default=0)  # Delay >= 60

    # Corruption Risk
    avg_corruption_risk = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    high_corruption_risk_count = models.IntegerField(default=0)  # Corruption >= 60

    class Meta:
        db_table = "analytics_historical_snapshot"
        ordering = ["-snapshot_date"]
        indexes = [
            models.Index(fields=["snapshot_date", "source_platform"]),
        ]
        verbose_name = "Historical Snapshot"
        verbose_name_plural = "Historical Snapshots"

    def __str__(self):
        return f"Snapshot {self.snapshot_date} - {self.source_platform} ({self.total_contracts} contracts)"


class RiskTrend(models.Model):
    """
    Detected risk trends over time.

    Identifies patterns like increasing overpricing, rising delays, etc.
    """

    TREND_TYPE_CHOICES = [
        ("OVERPRICING", "Overpricing Trend"),
        ("DELAY", "Delay Risk Trend"),
        ("CORRUPTION", "Corruption Risk Trend"),
        ("BUDGET_GROWTH", "Budget Growth Trend"),
        ("HIGH_RISK_INCREASE", "High Risk Contract Increase"),
    ]

    DIRECTION_CHOICES = [
        ("UP", "Increasing"),
        ("DOWN", "Decreasing"),
        ("STABLE", "Stable"),
    ]

    # Temporal info
    detected_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField()
    end_date = models.DateField()

    # Trend definition
    trend_type = models.CharField(max_length=30, choices=TREND_TYPE_CHOICES)
    source_platform = models.CharField(max_length=50)

    # Trend metrics
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    change_percent = models.DecimalField(max_digits=6, decimal_places=2)
    significance = models.CharField(
        max_length=20,
        choices=[("LOW", "Low"), ("MEDIUM", "Medium"), ("HIGH", "High"), ("CRITICAL", "Critical")],
    )

    # Details
    description = models.TextField()
    affected_contracts = models.IntegerField(default=0)
    severity_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    class Meta:
        db_table = "analytics_risk_trend"
        ordering = ["-detected_at"]
        indexes = [
            models.Index(fields=["trend_type", "start_date"]),
        ]

    def __str__(self):
        return f"{self.trend_type} ({self.direction}) - {self.start_date} to {self.end_date}"
