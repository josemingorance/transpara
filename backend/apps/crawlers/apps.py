"""Crawlers app configuration."""
from django.apps import AppConfig


class CrawlersConfig(AppConfig):
    """Configuration for crawlers app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.crawlers"
    verbose_name = "Crawlers"
