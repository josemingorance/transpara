"""Serializers for contracts API."""
from rest_framework import serializers

from apps.contracts.models import Contract, ContractAmendment, RawContractData
from apps.providers.models import Provider


class ProviderMinimalSerializer(serializers.ModelSerializer):
    """Minimal provider info for nested serialization."""

    class Meta:
        model = Provider
        fields = ["id", "name", "tax_id", "risk_score"]
        read_only_fields = fields


class ContractAmendmentSerializer(serializers.ModelSerializer):
    """Serializer for contract amendments."""

    amount_change_percentage = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = ContractAmendment
        fields = [
            "id",
            "amendment_type",
            "description",
            "previous_amount",
            "new_amount",
            "amount_change_percentage",
            "amendment_date",
            "reason",
            "created_at",
        ]
        read_only_fields = fields


class ContractListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for contract lists."""

    awarded_to = ProviderMinimalSerializer(read_only=True)
    overpricing_percentage = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )

    class Meta:
        model = Contract
        fields = [
            "id",
            "external_id",
            "title",
            "contract_type",
            "status",
            "budget",
            "awarded_amount",
            "overpricing_percentage",
            "risk_score",
            "is_overpriced",
            "publication_date",
            "deadline_date",
            "award_date",
            "contracting_authority",
            "awarded_to",
            "region",
            "province",
            "municipality",
            "source_platform",
        ]
        read_only_fields = fields


class ContractDetailSerializer(serializers.ModelSerializer):
    """Full contract details with all related data."""

    awarded_to = ProviderMinimalSerializer(read_only=True)
    amendments = ContractAmendmentSerializer(many=True, read_only=True)
    overpricing_percentage = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    has_high_risk = serializers.BooleanField(read_only=True)

    class Meta:
        model = Contract
        fields = [
            "id",
            "external_id",
            "title",
            "description",
            "contract_type",
            "status",
            "budget",
            "awarded_amount",
            "overpricing_percentage",
            "procedure_type",
            "publication_date",
            "deadline_date",
            "award_date",
            "contracting_authority",
            "awarded_to",
            "region",
            "province",
            "municipality",
            "source_url",
            "source_platform",
            # Risk analysis
            "risk_score",
            "corruption_risk",
            "delay_risk",
            "financial_risk",
            "has_high_risk",
            "is_overpriced",
            "has_amendments",
            "has_delays",
            "analyzed_at",
            "analysis_version",
            # Related
            "amendments",
            # Metadata
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ContractStatsSerializer(serializers.Serializer):
    """Serializer for contract statistics."""

    total_contracts = serializers.IntegerField()
    total_budget = serializers.DecimalField(max_digits=20, decimal_places=2)
    avg_budget = serializers.DecimalField(max_digits=20, decimal_places=2)
    high_risk_count = serializers.IntegerField()
    overpriced_count = serializers.IntegerField()
    avg_risk_score = serializers.DecimalField(max_digits=5, decimal_places=2)


class RawContractDataSerializer(serializers.ModelSerializer):
    """Serializer for raw contract data (admin use)."""

    contract = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = RawContractData
        fields = [
            "id",
            "source_platform",
            "external_id",
            "source_url",
            "is_processed",
            "processed_at",
            "processing_error",
            "contract",
            "created_at",
        ]
        read_only_fields = fields
