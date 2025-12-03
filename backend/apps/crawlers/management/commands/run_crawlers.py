"""
Django management command to run crawlers.

Usage:
    python manage.py run_crawlers                 # Run all crawlers
    python manage.py run_crawlers --only pcsp     # Run specific crawler
"""
from django.core.management.base import BaseCommand, CommandError

from apps.crawlers.registry import registry


class Command(BaseCommand):
    """Command to execute data collection crawlers."""

    help = "Run data collection crawlers"

    def add_arguments(self, parser) -> None:
        """Add command arguments."""
        parser.add_argument(
            "--only",
            type=str,
            help="Comma-separated list of crawler names to run",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="List all available crawlers",
        )
        parser.add_argument(
            "--incremental",
            action="store_true",
            help="Run in incremental mode (only fetch data since last successful run)",
        )
        parser.add_argument(
            "--since-date",
            type=str,
            help="Fetch data since this date (ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS). "
                 "Requires --incremental flag.",
        )

    def handle(self, *args, **options) -> None:
        """Execute the command."""
        # Import implementations to register them
        self._import_crawlers()

        # List crawlers if requested
        if options["list"]:
            self._list_crawlers()
            return

        # Determine which crawlers to run
        if options["only"]:
            crawler_names = [name.strip() for name in options["only"].split(",")]
        else:
            crawler_names = registry.list_all()

        if not crawler_names:
            raise CommandError("No crawlers available")

        # Validate incremental mode options
        incremental = options.get("incremental", False)
        since_date = options.get("since_date")

        if since_date and not incremental:
            raise CommandError("--since-date requires --incremental flag")

        # Run each crawler
        mode_str = "incremental" if incremental else "full"
        self.stdout.write(self.style.SUCCESS(f"\nRunning {len(crawler_names)} crawler(s) in {mode_str} mode...\n"))

        for name in crawler_names:
            self._run_crawler(name, incremental=incremental, since_date=since_date)

        self.stdout.write(self.style.SUCCESS("\n✓ All crawlers completed\n"))

    def _import_crawlers(self) -> None:
        """Import crawler implementations to register them."""
        try:
            # Import all crawler implementations
            from apps.crawlers.implementations import pcsp  # noqa: F401
        except ImportError as e:
            self.stdout.write(self.style.WARNING(f"Failed to import crawlers: {e}"))

    def _list_crawlers(self) -> None:
        """List all available crawlers."""
        crawlers = registry.list_all()

        if not crawlers:
            self.stdout.write(self.style.WARNING("No crawlers registered"))
            return

        self.stdout.write(self.style.SUCCESS("\nAvailable crawlers:"))
        for name in crawlers:
            crawler_class = registry.get(name)
            self.stdout.write(f"  • {name} ({crawler_class.source_platform})")
        self.stdout.write("")

    def _run_crawler(self, name: str, incremental: bool = False, since_date: str | None = None) -> None:
        """
        Run a single crawler.

        Args:
            name: Crawler name
            incremental: Whether to run in incremental mode
            since_date: Custom date for incremental fetch (ISO format)
        """
        crawler_class = registry.get(name)

        if not crawler_class:
            self.stdout.write(self.style.ERROR(f"✗ Crawler '{name}' not found"))
            return

        mode_suffix = " (incremental)" if incremental else ""
        self.stdout.write(f"Running: {name}{mode_suffix}...")

        try:
            crawler = crawler_class()

            # Pass incremental parameters to fetch_raw if supported
            if incremental:
                # Pass parameters using config that can be accessed in fetch_raw
                crawler.config['incremental'] = incremental
                if since_date:
                    crawler.config['since_date'] = since_date

                # Call fetch_raw with incremental parameters
                raw = crawler.fetch_raw(incremental=incremental, since_date=since_date)
                parsed = crawler.parse(raw)
                created, updated, failed = crawler.save(parsed)

                # Create run record manually
                from apps.crawlers.models import CrawlerRun
                from django.utils import timezone

                run = CrawlerRun.objects.create(
                    crawler_name=crawler.name,
                    status="SUCCESS" if failed == 0 else "PARTIAL",
                    started_at=timezone.now(),
                    completed_at=timezone.now(),
                    duration_seconds=0,
                    records_found=len(parsed),
                    records_created=created,
                    records_updated=updated,
                    records_failed=failed,
                    config={'incremental': incremental, 'since_date': since_date},
                )
            else:
                run = crawler.run_crawler()

            # Display results
            if run.status == "SUCCESS":
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✓ {name}: {run.records_created} created, "
                        f"{run.records_updated} updated "
                        f"({run.duration_seconds}s)"
                    )
                )
            elif run.status == "PARTIAL":
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ {name}: {run.records_created} created, "
                        f"{run.records_updated} updated, "
                        f"{run.records_failed} failed"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ {name}: {run.error_message}")
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ {name}: {e}"))
