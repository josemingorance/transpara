"""Contracts app configuration."""
from django.apps import AppConfig


class ContractsConfig(AppConfig):
    """Configuration for contracts app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.contracts"
    verbose_name = "Contracts"
