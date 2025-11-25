"""Admin interface for contracts app."""
from django.contrib import admin

from apps.contracts.models import Contract, ContractAmendment, RawContractData


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    """Admin for Contract model."""

    list_display = [
        "external_id",
        "title_short",
        "contract_type",
        "status",
        "budget",
        "risk_score",
        "is_overpriced",
        "publication_date",
    ]
    list_filter = [
        "status",
        "contract_type",
        "is_overpriced",
        "region",
        "source_platform",
    ]
    search_fields = [
        "title",
        "external_id",
        "contracting_authority",
        "description",
    ]
    readonly_fields = [
        "created_at",
        "updated_at",
        "analyzed_at",
    ]
    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "title",
                    "description",
                    "contract_type",
                    "status",
                )
            },
        ),
        (
            "Financial",
            {
                "fields": (
                    "budget",
                    "awarded_amount",
                )
            },
        ),
        (
            "Procurement",
            {
                "fields": (
                    "procedure_type",
                    "publication_date",
                    "deadline_date",
                    "award_date",
                )
            },
        ),
        (
            "Entities",
            {
                "fields": (
                    "contracting_authority",
                    "awarded_to",
                )
            },
        ),
        (
            "Location",
            {
                "fields": (
                    "region",
                    "province",
                    "municipality",
                )
            },
        ),
        (
            "Risk Analysis",
            {
                "fields": (
                    "risk_score",
                    "corruption_risk",
                    "delay_risk",
                    "financial_risk",
                    "is_overpriced",
                    "has_amendments",
                    "has_delays",
                )
            },
        ),
        (
            "Source",
            {
                "fields": (
                    "external_id",
                    "source_platform",
                    "source_url",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "analyzed_at",
                    "analysis_version",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def title_short(self, obj):
        """Truncate title for display."""
        return obj.title[:50] + "..." if len(obj.title) > 50 else obj.title

    title_short.short_description = "Title"


@admin.register(ContractAmendment)
class ContractAmendmentAdmin(admin.ModelAdmin):
    """Admin for ContractAmendment model."""

    list_display = [
        "contract",
        "amendment_type",
        "amendment_date",
        "previous_amount",
        "new_amount",
        "change_percentage",
    ]
    list_filter = ["amendment_type", "amendment_date"]
    search_fields = ["contract__title", "contract__external_id", "description"]
    raw_id_fields = ["contract"]

    def change_percentage(self, obj):
        """Display change percentage."""
        return f"{obj.amount_change_percentage:.2f}%"

    change_percentage.short_description = "Change %"


@admin.register(RawContractData)
class RawContractDataAdmin(admin.ModelAdmin):
    """Admin for RawContractData model."""

    list_display = [
        "external_id",
        "source_platform",
        "is_processed",
        "processed_at",
        "created_at",
    ]
    list_filter = [
        "source_platform",
        "is_processed",
        "created_at",
    ]
    search_fields = ["external_id", "source_url"]
    readonly_fields = ["created_at", "updated_at", "processed_at"]
    raw_id_fields = ["contract"]
