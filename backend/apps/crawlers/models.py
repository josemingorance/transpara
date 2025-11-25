"""Crawler models for tracking data collection."""
from django.db import models

from apps.core.models import TimeStampedModel


class CrawlerRun(TimeStampedModel):
    """
    Track crawler executions.

    Records when crawlers run, their status, and results
    for monitoring and debugging.
    """

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("RUNNING", "Running"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
        ("PARTIAL", "Partial Success"),
    ]

    crawler_name = models.CharField(max_length=100, db_index=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="PENDING", db_index=True
    )

    # Execution metadata
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True)

    # Results
    records_found = models.IntegerField(default=0)
    records_created = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)

    # Error tracking
    error_message = models.TextField(blank=True)
    error_traceback = models.TextField(blank=True)

    # Configuration
    config = models.JSONField(default=dict, help_text="Crawler configuration for this run")

    class Meta:
        verbose_name = "Crawler Run"
        verbose_name_plural = "Crawler Runs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["crawler_name", "status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.crawler_name} - {self.status} ({self.created_at})"

    @property
    def success_rate(self) -> float:
        """Calculate success rate of this run."""
        total = self.records_found
        if total == 0:
            return 0.0
        successful = self.records_created + self.records_updated
        return (successful / total) * 100
