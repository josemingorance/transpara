"""
Django management command to process raw contract data.

Usage:
    python manage.py process_raw_data                    # Process all unprocessed
    python manage.py process_raw_data --source PCSP      # Process specific source
    python manage.py process_raw_data --limit 100        # Limit number of records
    python manage.py process_raw_data --reprocess        # Reprocess all records
    python manage.py process_raw_data --enrich-providers # Also extract provider data
"""
import json
import logging
from django.core.management.base import BaseCommand

from apps.contracts.etl.normalizers import get_normalizer
from apps.contracts.models import RawContractData
from apps.providers.models import Provider
from apps.providers.enrichment import EnrichmentPipeline

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Command to process raw contract data through ETL pipeline."""

    help = "Process raw contract data and create normalized Contract records"

    def add_arguments(self, parser) -> None:
        """Add command arguments."""
        parser.add_argument(
            "--source",
            type=str,
            help="Process only records from specific source (e.g., PCSP, BOE)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Maximum number of records to process",
        )
        parser.add_argument(
            "--reprocess",
            action="store_true",
            help="Reprocess already processed records",
        )
        parser.add_argument(
            "--enrich-providers",
            action="store_true",
            help="Extract and enrich provider data from contracts",
        )

    def handle(self, *args, **options) -> None:
        """Execute the command."""
        # Store options for use in methods
        self.enrich_providers = options.get("enrich_providers", False)
        self.enrichment_pipeline = (
            EnrichmentPipeline() if self.enrich_providers else None
        )

        # Build queryset
        queryset = RawContractData.objects.all()

        if not options["reprocess"]:
            queryset = queryset.filter(is_processed=False)

        if options["source"]:
            queryset = queryset.filter(source_platform=options["source"])

        if options["limit"]:
            queryset = queryset[: options["limit"]]

        total = queryset.count()

        if total == 0:
            self.stdout.write(self.style.WARNING("No records to process"))
            return

        self.stdout.write(self.style.SUCCESS(f"\nProcessing {total} record(s)...\n"))

        # Process records
        processed = 0
        failed = 0
        providers_extracted = 0

        for raw_record in queryset:
            try:
                result = self._process_record(raw_record)
                if result:
                    processed += 1
                    self.stdout.write(f"  ✓ {raw_record.external_id}")

                    # Extract providers if flag is set
                    if self.enrich_providers:
                        extracted = self._extract_providers_from_record(raw_record)
                        providers_extracted += extracted
                else:
                    failed += 1
                    self.stdout.write(
                        self.style.WARNING(f"  ✗ {raw_record.external_id}: Failed")
                    )
            except Exception as e:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(f"  ✗ {raw_record.external_id}: {e}")
                )

        # Summary
        summary = f"\n✓ Completed: {processed} processed, {failed} failed"
        if self.enrich_providers:
            summary += f", {providers_extracted} providers extracted/enriched"
        summary += "\n"

        self.stdout.write(self.style.SUCCESS(summary))

    def _process_record(self, raw_record: RawContractData) -> bool:
        """
        Process a single raw record.

        Args:
            raw_record: RawContractData instance

        Returns:
            True if successful, False otherwise
        """
        normalizer = get_normalizer(raw_record.source_platform)

        if not normalizer:
            self.stdout.write(
                self.style.WARNING(
                    f"No normalizer for platform: {raw_record.source_platform}"
                )
            )
            return False

        contract = normalizer.process_raw_record(raw_record)
        return contract is not None

    def _extract_providers_from_record(self, raw_record: RawContractData) -> int:
        """
        Extract provider/company information from raw contract data.

        Args:
            raw_record: RawContractData instance

        Returns:
            Number of providers extracted/enriched
        """
        providers_found = []

        try:
            # Parse raw data - handle both dict and string formats
            if isinstance(raw_record.raw_data, str):
                data = json.loads(raw_record.raw_data)
            else:
                data = raw_record.raw_data

            # Extract from BOE contracts
            if raw_record.source_platform == "BOE":
                providers_found.extend(self._extract_from_boe_data(data))

            # Extract from PCSP contracts
            elif raw_record.source_platform == "PCSP":
                providers_found.extend(self._extract_from_pcsp_data(data))

        except Exception as e:
            logger.warning(f"Error extracting providers from {raw_record.external_id}: {e}")
            return 0

        # Create or update providers and enrich them
        enriched_count = 0
        for provider_data in providers_found:
            try:
                provider, created = Provider.objects.get_or_create(
                    tax_id=provider_data["tax_id"],
                    defaults={
                        "name": provider_data["name"],
                        "legal_name": provider_data.get("legal_name", provider_data["name"]),
                    },
                )

                # Update name if it changed
                if not created and provider.name != provider_data["name"]:
                    provider.name = provider_data["name"]
                    provider.legal_name = provider_data.get("legal_name", provider_data["name"])
                    provider.save(update_fields=["name", "legal_name"])

                # Enrich with external data if pipeline is available
                if self.enrichment_pipeline:
                    self.enrichment_pipeline.enrich(provider)

                enriched_count += 1

            except Exception as e:
                logger.warning(f"Error processing provider {provider_data.get('tax_id')}: {e}")

        return enriched_count

    def _extract_from_boe_data(self, data: dict) -> list:
        """
        Extract providers from BOE contract data.

        BOE contracts have: adjudicatario, licitadores, proveedores fields
        """
        providers = []

        # Extract adjudicatario (awarded to)
        if "adjudicatario" in data:
            adj = data["adjudicatario"]
            nif = adj.get("nif") or adj.get("NIF")
            nombre = adj.get("nombre") or adj.get("nombre_empresa")
            if nif and nombre:
                providers.append({"tax_id": nif, "name": nombre, "legal_name": nombre})

        # Extract licitadores (bidders)
        if "licitadores" in data:
            for licitador in data.get("licitadores", []):
                nif = licitador.get("nif") or licitador.get("NIF")
                nombre = licitador.get("nombre") or licitador.get("nombre_empresa")
                if nif and nombre:
                    providers.append({"tax_id": nif, "name": nombre, "legal_name": nombre})

        # Extract proveedores (suppliers)
        if "proveedores" in data:
            for proveedor in data.get("proveedores", []):
                nif = proveedor.get("nif") or proveedor.get("NIF")
                nombre = proveedor.get("nombre") or proveedor.get("nombre_empresa")
                if nif and nombre:
                    providers.append({"tax_id": nif, "name": nombre, "legal_name": nombre})

        return providers

    def _extract_from_pcsp_data(self, data: dict) -> list:
        """
        Extract providers from PCSP contract data.

        PCSP contracts have: empresa field with company info
        """
        providers = []

        if "empresa" in data:
            empresa = data["empresa"]
            nif = empresa.get("nif") or empresa.get("NIF")
            nombre = empresa.get("nombre") or empresa.get("nombre_empresa")
            if nif and nombre:
                providers.append({"tax_id": nif, "name": nombre, "legal_name": nombre})

        return providers
