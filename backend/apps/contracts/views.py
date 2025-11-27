"""Views for contracts API."""
from django.db.models import Avg, Count, Q, Sum
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.analytics.services.risk_calculator import RiskCalculator
from apps.contracts.models import Contract, ContractAmendment
from apps.contracts.serializers import (
    ContractAmendmentSerializer,
    ContractDetailSerializer,
    ContractListSerializer,
    ContractStatsSerializer,
)


class ContractFilter(filters.FilterSet):
    """Filter for contracts."""

    # Text search
    search = filters.CharFilter(method="filter_search")

    # Exact matches
    contract_type = filters.ChoiceFilter(choices=Contract._meta.get_field("contract_type").choices)
    status = filters.ChoiceFilter(choices=Contract._meta.get_field("status").choices)
    region = filters.CharFilter()
    province = filters.CharFilter()
    source_platform = filters.CharFilter()

    # Range filters
    budget_min = filters.NumberFilter(field_name="budget", lookup_expr="gte")
    budget_max = filters.NumberFilter(field_name="budget", lookup_expr="lte")
    risk_score_min = filters.NumberFilter(field_name="risk_score", lookup_expr="gte")
    risk_score_max = filters.NumberFilter(field_name="risk_score", lookup_expr="lte")

    # Date filters
    publication_date_after = filters.DateFilter(
        field_name="publication_date", lookup_expr="gte"
    )
    publication_date_before = filters.DateFilter(
        field_name="publication_date", lookup_expr="lte"
    )

    # Boolean filters
    is_overpriced = filters.BooleanFilter()
    has_amendments = filters.BooleanFilter()
    has_delays = filters.BooleanFilter()

    # Special filters
    high_risk = filters.BooleanFilter(method="filter_high_risk")

    class Meta:
        model = Contract
        fields = []

    def filter_search(self, queryset, name, value):
        """Full-text search across multiple fields."""
        return queryset.filter(
            Q(title__icontains=value)
            | Q(external_id__icontains=value)
            | Q(contracting_authority__icontains=value)
            | Q(description__icontains=value)
        )

    def filter_high_risk(self, queryset, name, value):
        """Filter contracts with risk_score > 70."""
        if value:
            return queryset.filter(risk_score__gt=70)
        return queryset


class ContractViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for contracts.

    Provides list and detail views with filtering, search, and ordering.
    """

    queryset = Contract.objects.select_related("awarded_to").order_by("-publication_date")
    filterset_class = ContractFilter
    search_fields = ["title", "external_id", "contracting_authority", "description"]
    ordering_fields = [
        "publication_date",
        "budget",
        "risk_score",
        "created_at",
    ]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "retrieve":
            return ContractDetailSerializer
        return ContractListSerializer

    @action(detail=False, methods=["get"])
    def stats(self, _request):
        """Get contract statistics."""
        queryset = self.filter_queryset(self.get_queryset())

        stats = queryset.aggregate(
            total_contracts=Count("id"),
            total_budget=Sum("budget"),
            avg_budget=Avg("budget"),
            high_risk_count=Count("id", filter=Q(risk_score__gt=70)),
            overpriced_count=Count("id", filter=Q(is_overpriced=True)),
            avg_risk_score=Avg("risk_score"),
        )

        serializer = ContractStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def amendments(self, request, pk=None):
        """
        Get contract amendments.

        Returns all amendments for a specific contract.
        """
        contract = self.get_object()
        amendments = contract.amendments.all()
        serializer = ContractAmendmentSerializer(amendments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def analyze(self, request, pk=None):
        """
        Trigger risk analysis for contract.

        Runs AI analysis and returns results.
        """
        contract = self.get_object()
        calculator = RiskCalculator()

        try:
            analysis = calculator.analyze_contract(contract)
            return Response(analysis)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    @action(detail=False, methods=["get"])
    def by_region(self, _request):
        """Group contracts by region."""
        queryset = self.filter_queryset(self.get_queryset())

        regions = (
            queryset.values("region")
            .annotate(
                count=Count("id"),
                total_budget=Sum("budget"),
                avg_risk_score=Avg("risk_score"),
                high_risk_count=Count("id", filter=Q(risk_score__gt=70)),
            )
            .order_by("-total_budget")
        )

        return Response(regions)

    @action(detail=False, methods=["get"])
    def by_type(self, _request):
        """Group contracts by type."""
        queryset = self.filter_queryset(self.get_queryset())

        types = (
            queryset.values("contract_type")
            .annotate(
                count=Count("id"),
                total_budget=Sum("budget"),
                avg_risk_score=Avg("risk_score"),
            )
            .order_by("-count")
        )

        return Response(types)


class ContractAmendmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for contract amendments.

    Read-only access to amendment history.
    """

    queryset = ContractAmendment.objects.select_related("contract").order_by(
        "-amendment_date"
    )
    serializer_class = ContractAmendmentSerializer
    filterset_fields = ["contract", "amendment_type"]
    ordering_fields = ["amendment_date", "new_amount"]
