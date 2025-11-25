"""
Django management command to run crawlers.

Usage:
    python manage.py run_crawlers                 # Run all crawlers
    python manage.py run_crawlers --only pcsp     # Run specific crawler
    python manage.py run_crawlers --only pcsp,boe # Run multiple crawlers
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

        # Run each crawler
        self.stdout.write(self.style.SUCCESS(f"\nRunning {len(crawler_names)} crawler(s)...\n"))

        for name in crawler_names:
            self._run_crawler(name)

        self.stdout.write(self.style.SUCCESS("\n✓ All crawlers completed\n"))

    def _import_crawlers(self) -> None:
        """Import crawler implementations to register them."""
        try:
            # Import all crawler implementations
            from apps.crawlers.implementations import pcsp  # noqa: F401

            # Add more imports as you create more crawlers
            # from apps.crawlers.implementations import boe, madrid, etc.
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

    def _run_crawler(self, name: str) -> None:
        """
        Run a single crawler.

        Args:
            name: Crawler name
        """
        crawler_class = registry.get(name)

        if not crawler_class:
            self.stdout.write(self.style.ERROR(f"✗ Crawler '{name}' not found"))
            return

        self.stdout.write(f"Running: {name}...")

        try:
            crawler = crawler_class()
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
