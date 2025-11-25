"""Admin interface for providers app."""
from django.contrib import admin

from apps.providers.models import Provider, ProviderAlert, ProviderRelationship


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    """Admin for Provider model."""

    list_display = [
        "name",
        "tax_id",
        "region",
        "total_contracts",
        "total_awarded_amount",
        "risk_score",
        "is_flagged",
    ]
    list_filter = [
        "region",
        "is_flagged",
        "industry",
    ]
    search_fields = [
        "name",
        "tax_id",
        "legal_name",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
        "total_contracts",
        "total_awarded_amount",
        "avg_contract_amount",
        "success_rate",
        "first_contract_date",
        "last_contract_date",
    ]
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "name",
                    "legal_name",
                    "tax_id",
                )
            },
        ),
        (
            "Contact",
            {
                "fields": (
                    "address",
                    "city",
                    "region",
                    "postal_code",
                    "phone",
                    "email",
                    "website",
                )
            },
        ),
        (
            "Business Information",
            {
                "fields": (
                    "industry",
                    "company_size",
                    "founded_year",
                )
            },
        ),
        (
            "Metrics",
            {
                "fields": (
                    "total_contracts",
                    "total_awarded_amount",
                    "avg_contract_amount",
                    "success_rate",
                    "first_contract_date",
                    "last_contract_date",
                )
            },
        ),
        (
            "Risk",
            {
                "fields": (
                    "risk_score",
                    "is_flagged",
                    "flag_reason",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )


@admin.register(ProviderRelationship)
class ProviderRelationshipAdmin(admin.ModelAdmin):
    """Admin for ProviderRelationship model."""

    list_display = [
        "provider_a",
        "provider_b",
        "relationship_type",
        "confidence",
        "created_at",
    ]
    list_filter = ["relationship_type", "confidence"]
    search_fields = [
        "provider_a__name",
        "provider_b__name",
    ]
    raw_id_fields = ["provider_a", "provider_b"]


@admin.register(ProviderAlert)
class ProviderAlertAdmin(admin.ModelAdmin):
    """Admin for ProviderAlert model."""

    list_display = [
        "provider",
        "severity",
        "alert_type",
        "title",
        "is_resolved",
        "created_at",
    ]
    list_filter = [
        "severity",
        "alert_type",
        "is_resolved",
        "created_at",
    ]
    search_fields = [
        "provider__name",
        "title",
        "description",
    ]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["provider"]
    fieldsets = (
        (
            "Alert Information",
            {
                "fields": (
                    "provider",
                    "severity",
                    "alert_type",
                    "title",
                    "description",
                    "evidence",
                )
            },
        ),
        (
            "Resolution",
            {
                "fields": (
                    "is_resolved",
                    "resolved_at",
                    "resolution_notes",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )
