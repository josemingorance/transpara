"""
Django management command to enrich provider data from external APIs.

This command queries PCSP (Plataforma de Contratación del Sector Público)
and other external APIs to extract and update provider information:
- Website
- Industry/Sector
- Company founding year
- Email and phone
- Company size
- Legal name

Usage:
    python manage.py enrich_providers                      # Enrich all providers
    python manage.py enrich_providers --limit 50           # Enrich first 50
    python manage.py enrich_providers --filter-region CA   # Only specific region
    python manage.py enrich_providers --filter-flagged     # Only flagged providers
    python manage.py enrich_providers --dry-run            # Simulate without saving
    python manage.py enrich_providers -v                   # Verbose output
"""

import logging
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.providers.enrichment import EnrichmentPipeline
from apps.providers.models import Provider

logger = logging.getLogger(__name__)


class ProviderBatchEnricher:
    """Orchestrate provider enrichment from external sources."""

    def __init__(self, verbose: bool = False, dry_run: bool = False):
        self.verbose = verbose
        self.dry_run = dry_run
        self.pipeline = EnrichmentPipeline(verbose=verbose)
        self.stats = {
            "total": 0,
            "enriched": 0,
            "with_website": 0,
            "with_industry": 0,
            "with_founding_year": 0,
            "with_email": 0,
            "with_phone": 0,
            "errors": 0,
        }

    def enrich_provider(self, provider: Provider) -> bool:
        """Enrich a single provider."""
        self.stats["total"] += 1

        try:
            # Query enrichment pipeline
            enriched_data = self.pipeline.enrich(provider.tax_id, provider.name)

            if not enriched_data.get("found"):
                if self.verbose:
                    logger.info(f"No enrichment found for {provider.name}")
                return False

            # Track what we're updating
            updated_fields = []
            updated = False

            # Update website
            if enriched_data.get("website") and not provider.website:
                provider.website = enriched_data["website"]
                updated = True
                updated_fields.append("website")
                self.stats["with_website"] += 1

            # Update industry
            if enriched_data.get("industry") and not provider.industry:
                provider.industry = enriched_data["industry"]
                updated = True
                updated_fields.append("industry")
                self.stats["with_industry"] += 1

            # Update founding year
            if enriched_data.get("founded_year") and not provider.founded_year:
                provider.founded_year = enriched_data["founded_year"]
                updated = True
                updated_fields.append("founded_year")
                self.stats["with_founding_year"] += 1

            # Update email
            if enriched_data.get("email") and not provider.email:
                provider.email = enriched_data["email"]
                updated = True
                updated_fields.append("email")
                self.stats["with_email"] += 1

            # Update phone
            if enriched_data.get("phone") and not provider.phone:
                provider.phone = enriched_data["phone"]
                updated = True
                updated_fields.append("phone")
                self.stats["with_phone"] += 1

            # Update company size
            if enriched_data.get("company_size") and not provider.company_size:
                provider.company_size = enriched_data["company_size"]
                updated = True
                updated_fields.append("company_size")

            # Update legal name
            if enriched_data.get("legal_name") and not provider.legal_name:
                provider.legal_name = enriched_data["legal_name"]
                updated = True
                updated_fields.append("legal_name")

            # Save changes
            if updated:
                if not self.dry_run:
                    provider.save(update_fields=updated_fields)
                    if self.verbose:
                        logger.info(
                            f"✓ Updated {provider.name}: {', '.join(updated_fields)}"
                        )
                self.stats["enriched"] += 1

            return updated

        except Exception as e:
            logger.error(f"Error enriching {provider.name}: {e}")
            self.stats["errors"] += 1
            return False

    def enrich_batch(self, providers: list[Provider]) -> dict:
        """Enrich a batch of providers."""
        for provider in providers:
            self.enrich_provider(provider)
        return self.stats


class Command(BaseCommand):
    """Management command to enrich provider data from external APIs."""

    help = "Enrich provider data from external APIs (PCSP, BOE, etc.)"

    def add_arguments(self, parser) -> None:
        """Add command arguments."""
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximum number of providers to enrich"
        )
        parser.add_argument(
            "--filter-region",
            type=str,
            default=None,
            help="Only enrich providers from specific region"
        )
        parser.add_argument(
            "--filter-flagged",
            action="store_true",
            help="Only enrich flagged providers"
        )
        parser.add_argument(
            "--filter-high-risk",
            action="store_true",
            help="Only enrich high-risk providers (risk_score > 70)"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate without saving to database"
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed enrichment progress"
        )

    def handle(self, *args, **options) -> None:
        """Execute the enrichment process."""
        verbose = options.get("verbose", False)
        dry_run = options.get("dry_run", False)
        limit = options.get("limit")
        region = options.get("filter_region")
        flagged_only = options.get("filter_flagged", False)
        high_risk_only = options.get("filter_high_risk", False)

        # Build query filters
        query = Q()

        if region:
            query &= Q(region__icontains=region)

        if flagged_only:
            query &= Q(is_flagged=True)

        if high_risk_only:
            query &= Q(risk_score__gt=Decimal("70"))

        # Fetch providers ordered by amount (process biggest first)
        providers = Provider.objects.filter(query).order_by("-total_awarded_amount")

        if limit:
            providers = providers[:limit]

        provider_count = providers.count()

        if provider_count == 0:
            self.stdout.write(
                self.style.WARNING("No providers found matching your criteria")
            )
            return

        # Display header
        mode = "[DRY RUN] " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(f"\n{mode}Enriching {provider_count} provider(s)...")
        )

        if verbose:
            self.stdout.write(
                self.style.HTTP_INFO(
                    f"  Querying: PCSP, BOE, and other external data sources\n"
                )
            )

        # Process providers
        enricher = ProviderBatchEnricher(verbose=verbose, dry_run=dry_run)
        stats = enricher.enrich_batch(list(providers))

        # Display results
        self._display_results(stats, dry_run)

    def _display_results(self, stats: dict, dry_run: bool) -> None:
        """Display enrichment results summary."""
        self.stdout.write(
            self.style.SUCCESS("\n" + "=" * 75)
        )
        self.stdout.write(
            self.style.SUCCESS("ENRICHMENT SUMMARY")
        )
        self.stdout.write(
            self.style.SUCCESS("=" * 75)
        )

        enriched_count = stats["enriched"]
        total_count = stats["total"]
        success_rate = (enriched_count / total_count * 100) if total_count > 0 else 0

        self.stdout.write(
            f"\n  Total processed:        {total_count}\n"
            f"  Successfully enriched:  {enriched_count} ({success_rate:.1f}%)\n"
            f"  \n"
            f"  Data added:\n"
            f"    • Websites:           {stats['with_website']}\n"
            f"    • Industries:         {stats['with_industry']}\n"
            f"    • Founding years:     {stats['with_founding_year']}\n"
            f"    • Email addresses:    {stats['with_email']}\n"
            f"    • Phone numbers:      {stats['with_phone']}\n"
            f"  \n"
            f"  Errors:                 {stats['errors']}\n"
        )

        self.stdout.write(
            self.style.SUCCESS("=" * 75 + "\n")
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️  DRY RUN MODE - Changes were simulated but NOT saved to database\n"
                )
            )

        if stats["errors"] > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  {stats['errors']} error(s) occurred during processing\n"
                )
            )
