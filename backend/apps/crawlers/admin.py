"""Admin interface for crawlers app."""
from django.contrib import admin
from django.utils.html import format_html

from apps.crawlers.models import CrawlerRun


@admin.register(CrawlerRun)
class CrawlerRunAdmin(admin.ModelAdmin):
    """Admin for CrawlerRun model."""

    list_display = [
        "crawler_name",
        "status_badge",
        "started_at",
        "duration_display",
        "records_found",
        "success_display",
    ]
    list_filter = [
        "status",
        "crawler_name",
        "created_at",
    ]
    search_fields = ["crawler_name", "error_message"]
    readonly_fields = [
        "crawler_name",
        "status",
        "started_at",
        "completed_at",
        "duration_seconds",
        "records_found",
        "records_created",
        "records_updated",
        "records_failed",
        "success_rate_display",
        "error_message",
        "error_traceback",
        "config",
        "created_at",
        "updated_at",
    ]
    fieldsets = (
        (
            "Execution",
            {
                "fields": (
                    "crawler_name",
                    "status",
                    "started_at",
                    "completed_at",
                    "duration_seconds",
                )
            },
        ),
        (
            "Results",
            {
                "fields": (
                    "records_found",
                    "records_created",
                    "records_updated",
                    "records_failed",
                    "success_rate_display",
                )
            },
        ),
        (
            "Configuration",
            {
                "fields": ("config",),
                "classes": ("collapse",),
            },
        ),
        (
            "Errors",
            {
                "fields": (
                    "error_message",
                    "error_traceback",
                ),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        """Disable manual creation."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable editing."""
        return False

    def status_badge(self, obj):
        """Display status with color badge."""
        colors = {
            "SUCCESS": "green",
            "RUNNING": "blue",
            "FAILED": "red",
            "PARTIAL": "orange",
            "PENDING": "gray",
        }
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.status,
        )

    status_badge.short_description = "Status"

    def duration_display(self, obj):
        """Display duration in human-readable format."""
        if obj.duration_seconds is None:
            return "-"
        seconds = obj.duration_seconds
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}m {seconds}s"

    duration_display.short_description = "Duration"

    def success_display(self, obj):
        """Display success rate."""
        rate = obj.success_rate
        if rate >= 90:
            color = "green"
        elif rate >= 70:
            color = "orange"
        else:
            color = "red"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>', color, rate
        )

    success_display.short_description = "Success Rate"

    def success_rate_display(self, obj):
        """Display detailed success rate."""
        return f"{obj.success_rate:.2f}%"

    success_rate_display.short_description = "Success Rate"
