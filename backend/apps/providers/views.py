"""Views for providers API."""
from django.db.models import Avg, Count, Q, Sum
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.analytics.services.risk_calculator import RiskCalculator
from apps.contracts.models import Contract
from apps.contracts.serializers import ContractListSerializer
from apps.providers.models import Provider, ProviderAlert, ProviderRelationship
from apps.providers.serializers import (
    ProviderAlertSerializer,
    ProviderDetailSerializer,
    ProviderListSerializer,
    ProviderRelationshipSerializer,
    ProviderStatsSerializer,
)


class ProviderFilter(filters.FilterSet):
    """Filter for providers."""

    # Text search
    search = filters.CharFilter(method="filter_search")

    # Exact matches
    region = filters.CharFilter()
    industry = filters.CharFilter()

    # Range filters
    total_contracts_min = filters.NumberFilter(field_name="total_contracts", lookup_expr="gte")
    total_contracts_max = filters.NumberFilter(field_name="total_contracts", lookup_expr="lte")
    risk_score_min = filters.NumberFilter(field_name="risk_score", lookup_expr="gte")
    risk_score_max = filters.NumberFilter(field_name="risk_score", lookup_expr="lte")

    # Boolean filters
    is_flagged = filters.BooleanFilter()
    high_risk = filters.BooleanFilter(method="filter_high_risk")

    class Meta:
        model = Provider
        fields = []

    def filter_search(self, queryset, name, value):
        """Full-text search across multiple fields."""
        return queryset.filter(
            Q(name__icontains=value)
            | Q(tax_id__icontains=value)
            | Q(legal_name__icontains=value)
        )

    def filter_high_risk(self, queryset, name, value):
        """Filter providers with risk_score > 70."""
        if value:
            return queryset.filter(risk_score__gt=70)
        return queryset


class ProviderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for providers.

    Provides list and detail views with filtering and search.
    """

    queryset = Provider.objects.order_by("-total_awarded_amount")
    filterset_class = ProviderFilter
    search_fields = ["name", "tax_id", "legal_name"]
    ordering_fields = [
        "total_contracts",
        "total_awarded_amount",
        "risk_score",
        "success_rate",
    ]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "retrieve":
            return ProviderDetailSerializer
        return ProviderListSerializer

    @action(detail=False, methods=["get"])
    def stats(self, _request):
        """Get provider statistics."""
        queryset = self.filter_queryset(self.get_queryset())

        stats = queryset.aggregate(
            total_providers=Count("id"),
            total_contracts=Sum("total_contracts"),
            total_awarded=Sum("total_awarded_amount"),
            flagged_count=Count("id", filter=Q(is_flagged=True)),
            high_risk_count=Count("id", filter=Q(risk_score__gt=70)),
            avg_success_rate=Avg("success_rate"),
        )

        serializer = ProviderStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def contracts(self, request, pk=None):
        """
        Get provider's contracts.

        Returns all contracts awarded to this provider.
        """
        provider = self.get_object()
        contracts = Contract.objects.filter(awarded_to=provider).order_by("-award_date")

        # Apply pagination
        page = self.paginate_queryset(contracts)
        if page is not None:
            serializer = ContractListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ContractListSerializer(contracts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def alerts(self, request, pk=None):
        """
        Get provider's alerts.

        Returns all alerts for this provider.
        """
        provider = self.get_object()
        alerts = provider.alerts.all().order_by("-created_at")
        serializer = ProviderAlertSerializer(alerts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def relationships(self, request, pk=None):
        """
        Get provider's relationships.

        Returns all flagged relationships for this provider.
        """
        provider = self.get_object()
        relationships = ProviderRelationship.objects.filter(
            Q(provider_a=provider) | Q(provider_b=provider)
        ).order_by("-confidence")

        serializer = ProviderRelationshipSerializer(relationships, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def analyze(self, request, pk=None):
        """
        Trigger risk analysis for provider.

        Runs AI analysis and returns results.
        """
        provider = self.get_object()
        calculator = RiskCalculator()

        try:
            analysis = calculator.analyze_provider(provider)
            return Response(analysis)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @action(detail=False, methods=["get"])
    def by_region(self, _request):
        """Group providers by region."""
        queryset = self.filter_queryset(self.get_queryset())

        regions = (
            queryset.values("region")
            .annotate(
                count=Count("id"),
                total_contracts=Sum("total_contracts"),
                total_awarded=Sum("total_awarded_amount"),
                avg_risk_score=Avg("risk_score"),
            )
            .order_by("-total_awarded")
        )

        return Response(regions)

    @action(detail=False, methods=["get"])
    def by_industry(self, _request):
        """Group providers by industry."""
        queryset = self.filter_queryset(self.get_queryset())

        industries = (
            queryset.values("industry")
            .annotate(
                count=Count("id"),
                total_contracts=Sum("total_contracts"),
                total_awarded=Sum("total_awarded_amount"),
            )
            .order_by("-count")
        )

        return Response(industries)


class ProviderAlertViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for provider alerts.

    Read-only access to alerts with filtering.
    """

    queryset = ProviderAlert.objects.select_related("provider").order_by("-created_at")
    serializer_class = ProviderAlertSerializer
    filterset_fields = ["provider", "severity", "alert_type", "is_resolved"]
    ordering_fields = ["created_at", "severity"]

    @action(detail=False, methods=["get"])
    def unresolved(self, request):
        """
        Get unresolved alerts.

        Returns all alerts that haven't been resolved yet.
        """
        alerts = self.get_queryset().filter(is_resolved=False)

        # Apply pagination
        page = self.paginate_queryset(alerts)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def critical(self, request):
        """
        Get critical alerts.

        Returns all critical severity alerts.
        """
        alerts = self.get_queryset().filter(severity="CRITICAL", is_resolved=False)
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)
