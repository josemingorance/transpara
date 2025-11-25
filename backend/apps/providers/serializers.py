"""Serializers for providers API."""
from rest_framework import serializers

from apps.providers.models import Provider, ProviderAlert, ProviderRelationship


class ProviderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for provider lists."""

    years_active = serializers.IntegerField(read_only=True)

    class Meta:
        model = Provider
        fields = [
            "id",
            "name",
            "tax_id",
            "region",
            "industry",
            "total_contracts",
            "total_awarded_amount",
            "avg_contract_amount",
            "success_rate",
            "risk_score",
            "is_flagged",
            "years_active",
            "last_contract_date",
        ]
        read_only_fields = fields


class ProviderDetailSerializer(serializers.ModelSerializer):
    """Full provider details."""

    years_active = serializers.IntegerField(read_only=True)
    has_high_risk = serializers.BooleanField(read_only=True)

    class Meta:
        model = Provider
        fields = [
            "id",
            "name",
            "tax_id",
            "legal_name",
            # Contact
            "address",
            "city",
            "region",
            "postal_code",
            "phone",
            "email",
            "website",
            # Business
            "industry",
            "company_size",
            "founded_year",
            # Metrics
            "total_contracts",
            "total_awarded_amount",
            "avg_contract_amount",
            "success_rate",
            "years_active",
            "first_contract_date",
            "last_contract_date",
            # Risk
            "risk_score",
            "has_high_risk",
            "is_flagged",
            "flag_reason",
            # Metadata
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ProviderAlertSerializer(serializers.ModelSerializer):
    """Serializer for provider alerts."""

    provider_name = serializers.CharField(source="provider.name", read_only=True)
    provider_tax_id = serializers.CharField(source="provider.tax_id", read_only=True)

    class Meta:
        model = ProviderAlert
        fields = [
            "id",
            "provider",
            "provider_name",
            "provider_tax_id",
            "severity",
            "alert_type",
            "title",
            "description",
            "evidence",
            "is_resolved",
            "resolved_at",
            "resolution_notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "provider_name", "provider_tax_id"]


class ProviderRelationshipSerializer(serializers.ModelSerializer):
    """Serializer for provider relationships."""

    provider_a_name = serializers.CharField(source="provider_a.name", read_only=True)
    provider_b_name = serializers.CharField(source="provider_b.name", read_only=True)

    class Meta:
        model = ProviderRelationship
        fields = [
            "id",
            "provider_a",
            "provider_a_name",
            "provider_b",
            "provider_b_name",
            "relationship_type",
            "confidence",
            "evidence",
            "created_at",
        ]
        read_only_fields = fields


class ProviderStatsSerializer(serializers.Serializer):
    """Serializer for provider statistics."""

    total_providers = serializers.IntegerField()
    total_contracts = serializers.IntegerField()
    total_awarded = serializers.DecimalField(max_digits=20, decimal_places=2)
    flagged_count = serializers.IntegerField()
    high_risk_count = serializers.IntegerField()
    avg_success_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
