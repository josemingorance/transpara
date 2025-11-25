"""
Django management command to process raw contract data.

Usage:
    python manage.py process_raw_data                    # Process all unprocessed
    python manage.py process_raw_data --source PCSP      # Process specific source
    python manage.py process_raw_data --limit 100        # Limit number of records
    python manage.py process_raw_data --reprocess        # Reprocess all records
"""
from django.core.management.base import BaseCommand

from apps.contracts.etl.normalizers import get_normalizer
from apps.contracts.models import RawContractData


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

    def handle(self, *args, **options) -> None:
        """Execute the command."""
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

        for raw_record in queryset:
            try:
                result = self._process_record(raw_record)
                if result:
                    processed += 1
                    self.stdout.write(f"  ✓ {raw_record.external_id}")
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
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Completed: {processed} processed, {failed} failed\n"
            )
        )

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
