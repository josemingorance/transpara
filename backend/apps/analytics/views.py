"""Views for analytics API."""
from datetime import timedelta

from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.analytics.serializers import (
    ContractTypeDistributionSerializer,
    DashboardStatsSerializer,
    RegionalStatsSerializer,
    TopProviderSerializer,
    TrendDataSerializer,
)
from apps.contracts.models import Contract
from apps.providers.models import Provider, ProviderAlert


class AnalyticsViewSet(viewsets.ViewSet):
    """
    ViewSet for analytics and dashboard data.

    Provides various statistical endpoints for dashboards and reports.
    """

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        """
        Get dashboard overview statistics.

        Returns comprehensive stats for the main dashboard.
        """
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)
        twenty_four_hours_ago = now - timedelta(hours=24)

        # Contract stats
        contracts = Contract.objects.all()
        contract_stats = contracts.aggregate(
            total=Count("id"),
            total_budget=Sum("budget"),
            high_risk=Count("id", filter=Q(risk_score__gt=70)),
            overpriced=Count("id", filter=Q(is_overpriced=True)),
            avg_risk=Avg("risk_score"),
            recent=Count("id", filter=Q(created_at__gte=thirty_days_ago)),
            analyzed_recent=Count("id", filter=Q(analyzed_at__gte=twenty_four_hours_ago)),
        )

        # Provider stats
        providers = Provider.objects.all()
        provider_stats = providers.aggregate(
            total=Count("id"),
            flagged=Count("id", filter=Q(is_flagged=True)),
        )

        # Alert stats
        critical_alerts = ProviderAlert.objects.filter(
            severity="CRITICAL", is_resolved=False
        ).count()

        # Combine all stats
        dashboard_data = {
            "total_contracts": contract_stats["total"] or 0,
            "total_budget": contract_stats["total_budget"] or 0,
            "high_risk_contracts": contract_stats["high_risk"] or 0,
            "overpriced_contracts": contract_stats["overpriced"] or 0,
            "total_providers": provider_stats["total"] or 0,
            "flagged_providers": provider_stats["flagged"] or 0,
            "avg_risk_score": contract_stats["avg_risk"] or 0,
            "critical_alerts": critical_alerts,
            "contracts_last_30_days": contract_stats["recent"] or 0,
            "analyzed_last_24_hours": contract_stats["analyzed_recent"] or 0,
        }

        serializer = DashboardStatsSerializer(dashboard_data)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def regional_stats(self, request):
        """
        Get statistics grouped by region.

        Returns contract stats for each region.
        """
        regional_data = (
            Contract.objects.values("region")
            .annotate(
                total_contracts=Count("id"),
                total_budget=Sum("budget"),
                avg_risk_score=Avg("risk_score"),
                high_risk_count=Count("id", filter=Q(risk_score__gt=70)),
                overpriced_count=Count("id", filter=Q(is_overpriced=True)),
            )
            .order_by("-total_budget")
        )

        serializer = RegionalStatsSerializer(regional_data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def trends(self, request):
        """
        Get trend data over time.

        Returns time series data for contracts by publication date.
        """
        # Get trend period from query params (default 90 days)
        days = int(request.query_params.get("days", 90))
        start_date = timezone.now().date() - timedelta(days=days)

        trends = (
            Contract.objects.filter(publication_date__gte=start_date)
            .values("publication_date")
            .annotate(
                count=Count("id"),
                total_amount=Sum("budget"),
                avg_risk_score=Avg("risk_score"),
            )
            .order_by("publication_date")
        )

        # Rename publication_date to date for serializer
        trend_data = [
            {
                "date": item["publication_date"],
                "count": item["count"],
                "total_amount": item["total_amount"] or 0,
                "avg_risk_score": item["avg_risk_score"] or 0,
            }
            for item in trends
        ]

        serializer = TrendDataSerializer(trend_data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def contract_type_distribution(self, request):
        """
        Get distribution of contracts by type.

        Returns stats for each contract type.
        """
        distribution = (
            Contract.objects.values("contract_type")
            .annotate(
                count=Count("id"),
                total_budget=Sum("budget"),
                avg_risk_score=Avg("risk_score"),
            )
            .order_by("-count")
        )

        serializer = ContractTypeDistributionSerializer(distribution, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def top_providers(self, request):
        """
        Get top providers by various metrics.

        Query params:
        - by: 'contracts' (default) or 'amount'
        - limit: number of results (default 10)
        """
        by = request.query_params.get("by", "contracts")
        limit = int(request.query_params.get("limit", 10))

        # Determine ordering
        if by == "amount":
            order_by = "-total_awarded_amount"
        else:
            order_by = "-total_contracts"

        providers = Provider.objects.order_by(order_by)[:limit]

        # Format data
        data = [
            {
                "provider_id": p.id,
                "provider_name": p.name,
                "provider_tax_id": p.tax_id,
                "total_contracts": p.total_contracts,
                "total_amount": p.total_awarded_amount,
                "risk_score": p.risk_score or 0,
            }
            for p in providers
        ]

        serializer = TopProviderSerializer(data, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def risk_distribution(self, request):
        """
        Get distribution of contracts by risk level.

        Returns count of contracts in each risk category.
        """
        contracts = Contract.objects.filter(risk_score__isnull=False)

        distribution = {
            "minimal": contracts.filter(risk_score__lt=20).count(),
            "low": contracts.filter(risk_score__gte=20, risk_score__lt=40).count(),
            "medium": contracts.filter(risk_score__gte=40, risk_score__lt=60).count(),
            "high": contracts.filter(risk_score__gte=60, risk_score__lt=75).count(),
            "critical": contracts.filter(risk_score__gte=75).count(),
        }

        return Response(distribution)

    @action(detail=False, methods=["get"])
    def alerts_summary(self, request):
        """
        Get summary of alerts by severity and type.

        Returns alert counts grouped by severity and type.
        """
        alerts = ProviderAlert.objects.filter(is_resolved=False)

        by_severity = (
            alerts.values("severity")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        by_type = (
            alerts.values("alert_type")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        return Response(
            {
                "by_severity": list(by_severity),
                "by_type": list(by_type),
                "total_unresolved": alerts.count(),
            }
        )

    @action(detail=False, methods=["get"])
    def recent_high_risk(self, request):
        """
        Get recent high-risk contracts.

        Returns contracts with risk_score > 70 from last 30 days.
        """
        thirty_days_ago = timezone.now() - timedelta(days=30)

        contracts = (
            Contract.objects.filter(
                risk_score__gt=70,
                created_at__gte=thirty_days_ago,
            )
            .select_related("awarded_to")
            .order_by("-risk_score")[:20]
        )

        from apps.contracts.serializers import ContractListSerializer

        serializer = ContractListSerializer(contracts, many=True)
        return Response(serializer.data)
