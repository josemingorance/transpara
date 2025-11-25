"""Serializers for analytics API."""
from rest_framework import serializers


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard overview statistics."""

    # Contract stats
    total_contracts = serializers.IntegerField()
    total_budget = serializers.DecimalField(max_digits=20, decimal_places=2)
    high_risk_contracts = serializers.IntegerField()
    overpriced_contracts = serializers.IntegerField()

    # Provider stats
    total_providers = serializers.IntegerField()
    flagged_providers = serializers.IntegerField()

    # Risk stats
    avg_risk_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    critical_alerts = serializers.IntegerField()

    # Recent activity
    contracts_last_30_days = serializers.IntegerField()
    analyzed_last_24_hours = serializers.IntegerField()


class RegionalStatsSerializer(serializers.Serializer):
    """Serializer for regional statistics."""

    region = serializers.CharField()
    total_contracts = serializers.IntegerField()
    total_budget = serializers.DecimalField(max_digits=20, decimal_places=2)
    avg_risk_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    high_risk_count = serializers.IntegerField()
    overpriced_count = serializers.IntegerField()


class TrendDataSerializer(serializers.Serializer):
    """Serializer for trend/time series data."""

    date = serializers.DateField()
    count = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    avg_risk_score = serializers.DecimalField(max_digits=5, decimal_places=2)


class RiskAnalysisSerializer(serializers.Serializer):
    """Serializer for detailed risk analysis."""

    overall = serializers.DictField()
    overpricing = serializers.DictField()
    corruption = serializers.DictField()
    delay = serializers.DictField()
    financial = serializers.DictField()


class ContractTypeDistributionSerializer(serializers.Serializer):
    """Serializer for contract type distribution."""

    contract_type = serializers.CharField()
    count = serializers.IntegerField()
    total_budget = serializers.DecimalField(max_digits=20, decimal_places=2)
    avg_risk_score = serializers.DecimalField(max_digits=5, decimal_places=2)


class TopProviderSerializer(serializers.Serializer):
    """Serializer for top providers by metric."""

    provider_id = serializers.IntegerField()
    provider_name = serializers.CharField()
    provider_tax_id = serializers.CharField()
    total_contracts = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    risk_score = serializers.DecimalField(max_digits=5, decimal_places=2)
