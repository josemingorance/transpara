"""
Django management command to recalculate provider metrics.

Usage:
    python manage.py recalculate_provider_metrics       # Recalculate all
    python manage.py recalculate_provider_metrics --id 36  # Single provider
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, DecimalField, F, Min, Max
from django.db.models.functions import Coalesce

from apps.providers.models import Provider
from apps.contracts.models import Contract


class Command(BaseCommand):
    """Command to recalculate provider metrics from related contracts."""

    help = "Recalculate provider metrics based on awarded contracts"

    def add_arguments(self, parser) -> None:
        """Add command arguments."""
        parser.add_argument(
            "--id",
            type=int,
            help="Recalculate metrics for specific provider by ID",
        )

    def handle(self, *args, **options) -> None:
        """Execute the command."""
        # Get providers to recalculate
        if options.get("id"):
            providers = Provider.objects.filter(id=options["id"])
        else:
            providers = Provider.objects.all()

        total = providers.count()

        if total == 0:
            self.stdout.write(self.style.WARNING("No providers to recalculate"))
            return

        self.stdout.write(
            self.style.SUCCESS(f"\nRecalculating metrics for {total} provider(s)...\n")
        )

        updated = 0
        for provider in providers:
            # Get all contracts where this provider was awarded_to
            contracts = Contract.objects.filter(awarded_to=provider)

            # Calculate metrics
            total_contracts = contracts.count()
            total_awarded = contracts.aggregate(
                total=Coalesce(Sum("awarded_amount"), 0, output_field=DecimalField())
            )["total"] or 0

            avg_contract = (
                total_awarded / total_contracts if total_contracts > 0 else 0
            )

            # For now, success_rate is the percentage of contracts (100% if has any)
            success_rate = 100 if total_contracts > 0 else 0

            # Get date range
            date_range = contracts.aggregate(
                first=Min("publication_date"),
                last=Max("publication_date"),
            )

            # Update provider
            provider.total_contracts = total_contracts
            provider.total_awarded_amount = total_awarded
            provider.avg_contract_amount = avg_contract
            provider.success_rate = success_rate
            provider.first_contract_date = date_range.get("first")
            provider.last_contract_date = date_range.get("last")
            provider.save(
                update_fields=[
                    "total_contracts",
                    "total_awarded_amount",
                    "avg_contract_amount",
                    "success_rate",
                    "first_contract_date",
                    "last_contract_date",
                ]
            )

            updated += 1
            self.stdout.write(
                f"  ✓ {provider.name}: {total_contracts} contracts, "
                f"€{total_awarded:,.2f} awarded"
            )

        self.stdout.write(
            self.style.SUCCESS(f"\n✓ Completed: {updated} provider(s) updated\n")
        )
