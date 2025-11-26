"""Django Admin configuration for Analytics app."""
from django.contrib import admin
from django.utils.html import format_html

from apps.analytics.models import HistoricalSnapshot, RiskTrend


@admin.register(HistoricalSnapshot)
class HistoricalSnapshotAdmin(admin.ModelAdmin):
    """Admin interface for Historical Snapshots with temporal analysis."""

    list_display = (
        "snapshot_date",
        "source_platform",
        "total_contracts_display",
        "avg_risk_display",
        "budget_display",
        "overpriced_display",
    )

    list_filter = (
        "source_platform",
        "snapshot_date",
    )

    search_fields = ("source_platform",)

    readonly_fields = (
        "created_at",
        "snapshot_summary",
        "risk_summary",
        "financial_summary",
        "contract_type_summary",
        "procedure_summary",
    )

    fieldsets = (
        (
            "Snapshot Info",
            {
                "fields": ("snapshot_date", "source_platform", "created_at"),
            },
        ),
        (
            "Contract Statistics",
            {
                "fields": (
                    "total_contracts",
                    "published_contracts",
                    "awarded_contracts",
                    "in_progress_contracts",
                    "completed_contracts",
                ),
            },
        ),
        (
            "Financial Data",
            {
                "fields": (
                    "total_budget",
                    "total_awarded",
                    "avg_budget",
                    "avg_awarded",
                    "financial_summary",
                ),
            },
        ),
        (
            "Risk Analysis",
            {
                "fields": (
                    "avg_risk_score",
                    "high_risk_count",
                    "medium_risk_count",
                    "low_risk_count",
                    "risk_summary",
                ),
            },
        ),
        (
            "Contract Types",
            {
                "fields": (
                    "works_count",
                    "services_count",
                    "supplies_count",
                    "mixed_count",
                    "other_count",
                    "contract_type_summary",
                ),
            },
        ),
        (
            "Procedure Types",
            {
                "fields": (
                    "open_procedure_count",
                    "restricted_procedure_count",
                    "negotiated_procedure_count",
                    "procedure_summary",
                ),
            },
        ),
        (
            "Risk Details",
            {
                "fields": (
                    "overpriced_count",
                    "avg_overpricing_risk",
                    "avg_delay_risk",
                    "high_delay_risk_count",
                    "avg_corruption_risk",
                    "high_corruption_risk_count",
                ),
            },
        ),
    )

    ordering = ("-snapshot_date",)
    date_hierarchy = "snapshot_date"

    def total_contracts_display(self, obj):
        """Display total contracts with formatting."""
        return f"{obj.total_contracts:,}"

    total_contracts_display.short_description = "Total Contracts"

    def avg_risk_display(self, obj):
        """Display average risk with color coding."""
        risk = float(obj.avg_risk_score)
        if risk >= 60:
            color = "red"
            level = "🔴 HIGH"
        elif risk >= 40:
            color = "orange"
            level = "🟠 MEDIUM"
        else:
            color = "green"
            level = "🟢 LOW"

        risk_str = f"{risk:.1f}"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ({})</span>',
            color,
            level,
            risk_str,
        )

    avg_risk_display.short_description = "Avg Risk"

    def budget_display(self, obj):
        """Display total budget."""
        budget = float(obj.total_budget)
        budget_str = f"€{budget:,.0f}"
        return format_html('<strong>{}</strong>', budget_str)

    budget_display.short_description = "Total Budget"

    def overpriced_display(self, obj):
        """Display overpriced contract count."""
        return format_html(
            '<span style="color: orange;">🔶 {} contracts</span>',
            obj.overpriced_count,
        )

    overpriced_display.short_description = "Overpriced"

    def snapshot_summary(self, obj):
        """Summary of snapshot."""
        return format_html(
            "<h3>Snapshot: {}</h3>"
            "<p><strong>Date:</strong> {}</p>"
            "<p><strong>Total Contracts:</strong> {:,}</p>"
            "<p><strong>Source:</strong> {}</p>",
            obj.snapshot_date,
            obj.snapshot_date.strftime("%B %d, %Y"),
            obj.total_contracts,
            obj.source_platform,
        )

    snapshot_summary.short_description = "Snapshot Summary"

    def risk_summary(self, obj):
        """Summary of risk metrics."""
        return format_html(
            "<table style='width: 100%;'>"
            "<tr><td><strong>Average Risk:</strong></td><td>{:.2f}/100</td></tr>"
            "<tr><td><strong>High Risk (≥60):</strong></td><td style='color: red;'>{}</td></tr>"
            "<tr><td><strong>Medium Risk (40-60):</strong></td><td style='color: orange;'>{}</td></tr>"
            "<tr><td><strong>Low Risk (20-40):</strong></td><td style='color: green;'>{}</td></tr>"
            "</table>",
            obj.avg_risk_score,
            obj.high_risk_count,
            obj.medium_risk_count,
            obj.low_risk_count,
        )

    risk_summary.short_description = "Risk Summary"

    def financial_summary(self, obj):
        """Summary of financial metrics."""
        return format_html(
            "<table style='width: 100%;'>"
            "<tr><td><strong>Total Budget:</strong></td><td>€{:,.0f}</td></tr>"
            "<tr><td><strong>Total Awarded:</strong></td><td>€{:,.0f}</td></tr>"
            "<tr><td><strong>Average Budget:</strong></td><td>€{:,.0f}</td></tr>"
            "<tr><td><strong>Average Awarded:</strong></td><td>€{:,.0f}</td></tr>"
            "</table>",
            obj.total_budget,
            obj.total_awarded,
            obj.avg_budget,
            obj.avg_awarded,
        )

    financial_summary.short_description = "Financial Summary"

    def contract_type_summary(self, obj):
        """Summary of contract types."""
        return format_html(
            "<table style='width: 100%;'>"
            "<tr><td><strong>Works:</strong></td><td>{}</td></tr>"
            "<tr><td><strong>Services:</strong></td><td>{}</td></tr>"
            "<tr><td><strong>Supplies:</strong></td><td>{}</td></tr>"
            "<tr><td><strong>Mixed:</strong></td><td>{}</td></tr>"
            "<tr><td><strong>Other:</strong></td><td>{}</td></tr>"
            "</table>",
            obj.works_count,
            obj.services_count,
            obj.supplies_count,
            obj.mixed_count,
            obj.other_count,
        )

    contract_type_summary.short_description = "Contract Type Distribution"

    def procedure_summary(self, obj):
        """Summary of procedure types."""
        return format_html(
            "<table style='width: 100%;'>"
            "<tr><td><strong>Open:</strong></td><td>{}</td></tr>"
            "<tr><td><strong>Restricted:</strong></td><td>{}</td></tr>"
            "<tr><td><strong>Negotiated:</strong></td><td>{}</td></tr>"
            "</table>",
            obj.open_procedure_count,
            obj.restricted_procedure_count,
            obj.negotiated_procedure_count,
        )

    procedure_summary.short_description = "Procedure Type Distribution"


@admin.register(RiskTrend)
class RiskTrendAdmin(admin.ModelAdmin):
    """Admin interface for Risk Trends."""

    list_display = (
        "detected_at",
        "trend_type",
        "direction_icon",
        "significance_badge",
        "change_percent_display",
        "date_range",
    )

    list_filter = (
        "trend_type",
        "significance",
        "direction",
        "detected_at",
    )

    search_fields = (
        "description",
        "source_platform",
    )

    readonly_fields = (
        "detected_at",
        "trend_summary",
    )

    fieldsets = (
        (
            "Trend Info",
            {
                "fields": ("trend_type", "source_platform", "detected_at"),
            },
        ),
        (
            "Time Range",
            {
                "fields": ("start_date", "end_date"),
            },
        ),
        (
            "Trend Analysis",
            {
                "fields": (
                    "direction",
                    "change_percent",
                    "significance",
                    "severity_score",
                ),
            },
        ),
        (
            "Impact",
            {
                "fields": ("description", "affected_contracts"),
            },
        ),
    )

    ordering = ("-detected_at",)

    def direction_icon(self, obj):
        """Display direction with icon."""
        if obj.direction == "UP":
            return format_html('📈 <span style="color: red;"><strong>Increasing</strong></span>')
        elif obj.direction == "DOWN":
            return format_html('📉 <span style="color: green;"><strong>Decreasing</strong></span>')
        else:
            return "➡️ Stable"

    direction_icon.short_description = "Direction"

    def significance_badge(self, obj):
        """Display significance with badge."""
        colors = {
            "CRITICAL": "red",
            "HIGH": "orange",
            "MEDIUM": "orange",
            "LOW": "green",
        }
        color = colors.get(obj.significance, "gray")
        symbols = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
        }
        symbol = symbols.get(obj.significance, "⚪")

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{} {}</span>',
            color,
            symbol,
            obj.get_significance_display(),
        )

    significance_badge.short_description = "Severity"

    def change_percent_display(self, obj):
        """Display change percent with sign."""
        if obj.direction == "UP":
            color = "red"
            sign = "+"
        else:
            color = "green"
            sign = ""

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}{:.1f}%</span>',
            color,
            sign,
            obj.change_percent,
        )

    change_percent_display.short_description = "Change"

    def date_range(self, obj):
        """Display date range."""
        return f"{obj.start_date} to {obj.end_date}"

    date_range.short_description = "Date Range"

    def trend_summary(self, obj):
        """Summary of trend."""
        return format_html(
            "<h3>{} - {}</h3>"
            "<p><strong>Period:</strong> {} to {}</p>"
            "<p><strong>Change:</strong> {}{:.1f}%</p>"
            "<p><strong>Affected Contracts:</strong> {}</p>"
            "<p><strong>Description:</strong> {}</p>",
            obj.get_trend_type_display(),
            obj.get_direction_display(),
            obj.start_date,
            obj.end_date,
            "+" if obj.direction == "UP" else "",
            obj.change_percent,
            obj.affected_contracts,
            obj.description,
        )

    trend_summary.short_description = "Trend Summary"
