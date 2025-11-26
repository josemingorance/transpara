"""
Historical data analyzer for temporal trend detection.

Generates snapshots of contract metrics over time and detects trends.
"""
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from django.db.models import Count, Avg, Sum, Q

from apps.analytics.models import HistoricalSnapshot, RiskTrend
from apps.contracts.models import Contract

logger = logging.getLogger(__name__)


class HistoricalAnalyzer:
    """Generate and analyze historical contract metrics."""

    def __init__(self):
        self.logger = logger

    def create_snapshot(self, snapshot_date, source_platform="ALL"):
        """
        Create a historical snapshot for a specific date and platform.

        Args:
            snapshot_date: Date for the snapshot
            source_platform: "BOE", "PCSP", or "ALL"

        Returns:
            HistoricalSnapshot instance
        """
        self.logger.info(f"Creating snapshot for {snapshot_date} ({source_platform})")

        # Build base queryset
        if source_platform == "ALL":
            contracts = Contract.objects.all()
        else:
            contracts = Contract.objects.filter(source_platform=source_platform)

        # Filter by publication date <= snapshot_date
        contracts = contracts.filter(publication_date__lte=snapshot_date)

        if not contracts.exists():
            self.logger.warning(f"No contracts found for {snapshot_date}")
            return None

        # Calculate metrics
        metrics = self._calculate_metrics(contracts)

        # Create or update snapshot
        snapshot, created = HistoricalSnapshot.objects.update_or_create(
            snapshot_date=snapshot_date,
            source_platform=source_platform,
            defaults=metrics,
        )

        self.logger.info(f"{'Created' if created else 'Updated'} snapshot with {metrics['total_contracts']} contracts")
        return snapshot

    def _calculate_metrics(self, queryset):
        """Calculate all metrics for a contract queryset."""
        total = queryset.count()

        if total == 0:
            return {
                "total_contracts": 0,
                "published_contracts": 0,
                "awarded_contracts": 0,
                "in_progress_contracts": 0,
                "completed_contracts": 0,
                "total_budget": Decimal("0"),
                "total_awarded": Decimal("0"),
                "avg_budget": Decimal("0"),
                "avg_awarded": Decimal("0"),
                "avg_risk_score": Decimal("0"),
                "high_risk_count": 0,
                "medium_risk_count": 0,
                "low_risk_count": 0,
            }

        return {
            # Status counts
            "total_contracts": total,
            "published_contracts": queryset.filter(status="PUBLISHED").count(),
            "awarded_contracts": queryset.filter(status="AWARDED").count(),
            "in_progress_contracts": queryset.filter(status="IN_PROGRESS").count(),
            "completed_contracts": queryset.filter(status="COMPLETED").count(),
            # Financial
            "total_budget": queryset.aggregate(Sum("budget"))["budget__sum"] or Decimal("0"),
            "total_awarded": queryset.aggregate(Sum("awarded_amount"))["awarded_amount__sum"] or Decimal("0"),
            "avg_budget": queryset.aggregate(Avg("budget"))["budget__avg"] or Decimal("0"),
            "avg_awarded": queryset.aggregate(Avg("awarded_amount"))["awarded_amount__avg"] or Decimal("0"),
            # Risk
            "avg_risk_score": queryset.aggregate(Avg("risk_score"))["risk_score__avg"] or Decimal("0"),
            "high_risk_count": queryset.filter(risk_score__gte=60).count(),
            "medium_risk_count": queryset.filter(risk_score__gte=40, risk_score__lt=60).count(),
            "low_risk_count": queryset.filter(risk_score__gte=20, risk_score__lt=40).count(),
            # Types
            "works_count": queryset.filter(contract_type="WORKS").count(),
            "services_count": queryset.filter(contract_type="SERVICES").count(),
            "supplies_count": queryset.filter(contract_type="SUPPLIES").count(),
            "mixed_count": queryset.filter(contract_type="MIXED").count(),
            "other_count": queryset.filter(contract_type="OTHER").count(),
            # Procedures
            "open_procedure_count": queryset.filter(procedure_type="OPEN").count(),
            "restricted_procedure_count": queryset.filter(procedure_type="RESTRICTED").count(),
            "negotiated_procedure_count": queryset.filter(procedure_type="NEGOTIATED").count(),
            # Overpricing
            "overpriced_count": queryset.filter(is_overpriced=True).count(),
            "avg_overpricing_risk": queryset.aggregate(Avg("financial_risk"))["financial_risk__avg"] or Decimal("0"),
            # Delays
            "avg_delay_risk": queryset.aggregate(Avg("delay_risk"))["delay_risk__avg"] or Decimal("0"),
            "high_delay_risk_count": queryset.filter(delay_risk__gte=60).count(),
            # Corruption
            "avg_corruption_risk": queryset.aggregate(Avg("corruption_risk"))["corruption_risk__avg"] or Decimal("0"),
            "high_corruption_risk_count": queryset.filter(corruption_risk__gte=60).count(),
        }

    def analyze_trends(self, start_date, end_date, source_platform="ALL"):
        """
        Detect trends over a date range.

        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            source_platform: "BOE", "PCSP", or "ALL"

        Returns:
            List of RiskTrend instances
        """
        self.logger.info(f"Analyzing trends from {start_date} to {end_date}")

        # Get snapshots for the period
        snapshots = HistoricalSnapshot.objects.filter(
            snapshot_date__gte=start_date,
            snapshot_date__lte=end_date,
            source_platform=source_platform,
        ).order_by("snapshot_date")

        if snapshots.count() < 2:
            self.logger.warning(f"Not enough snapshots to detect trends ({snapshots.count()} found)")
            return []

        trends = []

        # Analyze each trend type
        trend_types = [
            ("OVERPRICING", self._detect_overpricing_trend),
            ("DELAY", self._detect_delay_trend),
            ("CORRUPTION", self._detect_corruption_trend),
            ("BUDGET_GROWTH", self._detect_budget_growth_trend),
            ("HIGH_RISK_INCREASE", self._detect_high_risk_trend),
        ]

        for trend_type, detector_func in trend_types:
            trend = detector_func(snapshots, start_date, end_date, source_platform)
            if trend:
                trends.append(trend)

        self.logger.info(f"Detected {len(trends)} trends")
        return trends

    def _detect_overpricing_trend(self, snapshots, start_date, end_date, source_platform):
        """Detect if overpricing is increasing."""
        first = snapshots.first()
        last = snapshots.last()

        if not first or not last:
            return None

        change = float(last.avg_overpricing_risk) - float(first.avg_overpricing_risk)
        change_percent = (change / float(first.avg_overpricing_risk) * 100) if first.avg_overpricing_risk > 0 else 0

        if abs(change_percent) < 5:  # Less than 5% change
            direction = "STABLE"
            significance = "LOW"
        elif change > 0:
            direction = "UP"
            significance = "HIGH" if change_percent > 20 else "MEDIUM"
        else:
            direction = "DOWN"
            significance = "MEDIUM"

        if direction == "STABLE":
            return None

        return RiskTrend.objects.create(
            trend_type="OVERPRICING",
            source_platform=source_platform,
            start_date=start_date,
            end_date=end_date,
            direction=direction,
            change_percent=Decimal(str(change_percent)),
            significance=significance,
            description=f"Overpricing risk changed by {change_percent:.1f}% from {float(first.avg_overpricing_risk):.1f} to {float(last.avg_overpricing_risk):.1f}",
            affected_contracts=last.overpriced_count,
            severity_score=Decimal(str(abs(change_percent))),
        )

    def _detect_delay_trend(self, snapshots, start_date, end_date, source_platform):
        """Detect if delay risk is increasing."""
        first = snapshots.first()
        last = snapshots.last()

        if not first or not last:
            return None

        change = float(last.avg_delay_risk) - float(first.avg_delay_risk)
        change_percent = (change / float(first.avg_delay_risk) * 100) if first.avg_delay_risk > 0 else 0

        if abs(change_percent) < 5:
            return None

        direction = "UP" if change > 0 else "DOWN"
        significance = "CRITICAL" if abs(change_percent) > 30 else "HIGH" if abs(change_percent) > 15 else "MEDIUM"

        return RiskTrend.objects.create(
            trend_type="DELAY",
            source_platform=source_platform,
            start_date=start_date,
            end_date=end_date,
            direction=direction,
            change_percent=Decimal(str(change_percent)),
            significance=significance,
            description=f"Delay risk changed by {change_percent:.1f}% - High delay risk contracts: {last.high_delay_risk_count}",
            affected_contracts=last.high_delay_risk_count,
            severity_score=Decimal(str(abs(change_percent))),
        )

    def _detect_corruption_trend(self, snapshots, start_date, end_date, source_platform):
        """Detect if corruption risk is increasing."""
        first = snapshots.first()
        last = snapshots.last()

        if not first or not last:
            return None

        change_count = last.high_corruption_risk_count - first.high_corruption_risk_count
        change_percent = (change_count / max(first.high_corruption_risk_count, 1)) * 100

        if abs(change_percent) < 5:
            return None

        direction = "UP" if change_count > 0 else "DOWN"
        significance = "CRITICAL" if abs(change_percent) > 25 else "HIGH"

        return RiskTrend.objects.create(
            trend_type="CORRUPTION",
            source_platform=source_platform,
            start_date=start_date,
            end_date=end_date,
            direction=direction,
            change_percent=Decimal(str(change_percent)),
            significance=significance,
            description=f"High corruption risk contracts increased by {change_count} ({change_percent:.1f}%)",
            affected_contracts=last.high_corruption_risk_count,
            severity_score=Decimal(str(abs(change_percent))),
        )

    def _detect_budget_growth_trend(self, snapshots, start_date, end_date, source_platform):
        """Detect if budgets are growing."""
        first = snapshots.first()
        last = snapshots.last()

        if not first or not last:
            return None

        budget_change = float(last.total_budget) - float(first.total_budget)
        budget_change_percent = (budget_change / float(first.total_budget) * 100) if first.total_budget > 0 else 0

        if abs(budget_change_percent) < 5:
            return None

        direction = "UP" if budget_change > 0 else "DOWN"
        significance = "HIGH" if abs(budget_change_percent) > 30 else "MEDIUM"

        return RiskTrend.objects.create(
            trend_type="BUDGET_GROWTH",
            source_platform=source_platform,
            start_date=start_date,
            end_date=end_date,
            direction=direction,
            change_percent=Decimal(str(budget_change_percent)),
            significance=significance,
            description=f"Total budget changed by {budget_change_percent:.1f}% - From €{float(first.total_budget):,.0f} to €{float(last.total_budget):,.0f}",
            affected_contracts=last.total_contracts,
            severity_score=Decimal(str(abs(budget_change_percent))),
        )

    def _detect_high_risk_trend(self, snapshots, start_date, end_date, source_platform):
        """Detect if high-risk contracts are increasing."""
        first = snapshots.first()
        last = snapshots.last()

        if not first or not last:
            return None

        change_count = last.high_risk_count - first.high_risk_count
        change_percent = (change_count / max(first.high_risk_count, 1)) * 100 if first.high_risk_count > 0 else 100

        if change_count == 0:
            return None

        direction = "UP" if change_count > 0 else "DOWN"
        significance = "CRITICAL" if change_percent > 50 else "HIGH" if change_percent > 25 else "MEDIUM"

        return RiskTrend.objects.create(
            trend_type="HIGH_RISK_INCREASE",
            source_platform=source_platform,
            start_date=start_date,
            end_date=end_date,
            direction=direction,
            change_percent=Decimal(str(change_percent)),
            significance=significance,
            description=f"High-risk contracts ({change_count:+d}) - Now {last.high_risk_count} contracts at risk >= 60",
            affected_contracts=last.high_risk_count,
            severity_score=Decimal(str(min(abs(change_percent), 100))),
        )
