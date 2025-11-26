"""
Django management command to fetch and analyze historical contract data.

Usage:
    python manage.py fetch_historical_data --months 6
    python manage.py fetch_historical_data --from-date 2025-06-01 --to-date 2025-11-30
    python manage.py fetch_historical_data --months 3 --source pcsp
    python manage.py fetch_historical_data --months 6 --analyze-trends
"""
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

from apps.analytics.services.historical_analyzer import HistoricalAnalyzer


class Command(BaseCommand):
    """Command to fetch and analyze historical contract data."""

    help = "Generate historical snapshots and detect trends in contract data"

    def add_arguments(self, parser) -> None:
        """Add command arguments."""
        parser.add_argument(
            "--months",
            type=int,
            default=6,
            help="Number of months to analyze (default: 6)",
        )
        parser.add_argument(
            "--from-date",
            type=str,
            help="Start date (YYYY-MM-DD format)",
        )
        parser.add_argument(
            "--to-date",
            type=str,
            help="End date (YYYY-MM-DD format)",
        )
        parser.add_argument(
            "--source",
            type=str,
            choices=["boe", "pcsp", "all"],
            default="all",
            help="Data source to analyze (default: all)",
        )
        parser.add_argument(
            "--analyze-trends",
            action="store_true",
            help="Analyze and detect trends",
        )
        parser.add_argument(
            "--daily",
            action="store_true",
            help="Create daily snapshots (default: monthly)",
        )

    def handle(self, *args, **options) -> None:
        """Execute the command."""
        analyzer = HistoricalAnalyzer()

        # Determine date range
        if options["from_date"] and options["to_date"]:
            try:
                start_date = datetime.strptime(options["from_date"], "%Y-%m-%d").date()
                end_date = datetime.strptime(options["to_date"], "%Y-%m-%d").date()
            except ValueError:
                self.stdout.write(self.style.ERROR("Invalid date format. Use YYYY-MM-DD"))
                return
        else:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30 * options["months"])

        self.stdout.write(
            self.style.SUCCESS(
                f"\n📊 Historical Data Analysis\n"
                f"Period: {start_date} to {end_date}\n"
                f"Source: {options['source'].upper()}\n"
            )
        )

        # Map source
        source_map = {
            "boe": "BOE",
            "pcsp": "PCSP",
            "all": "ALL",
        }
        source_platform = source_map[options["source"]]

        # Create snapshots
        self._create_snapshots(analyzer, start_date, end_date, source_platform, options["daily"])

        # Analyze trends if requested
        if options["analyze_trends"]:
            self._analyze_trends(analyzer, start_date, end_date, source_platform)

        self.stdout.write(self.style.SUCCESS("\n✓ Historical analysis completed\n"))

    def _create_snapshots(self, analyzer, start_date, end_date, source_platform, daily=False):
        """Create snapshots for the date range."""
        self.stdout.write("\n📸 Creating Historical Snapshots...\n")

        # Determine step
        step = timedelta(days=1) if daily else timedelta(days=1)  # Always daily for accuracy
        current_date = start_date

        snapshot_count = 0
        created_count = 0

        while current_date <= end_date:
            try:
                snapshot = analyzer.create_snapshot(current_date, source_platform)
                if snapshot:
                    snapshot_count += 1
                    if snapshot_count % 10 == 0:
                        self.stdout.write(f"  ✓ {current_date}: {snapshot.total_contracts} contracts")

                current_date += step

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠ Failed to create snapshot for {current_date}: {e}")
                )
                current_date += step

        self.stdout.write(
            f"\n✓ Created {snapshot_count} snapshots for {source_platform}\n"
        )

    def _analyze_trends(self, analyzer, start_date, end_date, source_platform):
        """Analyze and detect trends."""
        self.stdout.write("📈 Analyzing Trends...\n")

        trends = analyzer.analyze_trends(start_date, end_date, source_platform)

        if not trends:
            self.stdout.write(self.style.WARNING("  No significant trends detected\n"))
            return

        for trend in trends:
            # Color based on severity
            if trend.significance == "CRITICAL":
                symbol = "🔴"
                style = self.style.ERROR
            elif trend.significance == "HIGH":
                symbol = "🟠"
                style = self.style.WARNING
            else:
                symbol = "🟡"
                style = self.style.SUCCESS

            direction_symbol = "📈" if trend.direction == "UP" else "📉"

            output = (
                f"{symbol} {trend.get_trend_type_display()}\n"
                f"   {direction_symbol} {trend.direction}: {trend.change_percent:.1f}%\n"
                f"   Severity: {trend.significance}\n"
                f"   {trend.description}\n"
                f"   Affected Contracts: {trend.affected_contracts}\n"
            )

            self.stdout.write(style(output))

        self.stdout.write(
            self.style.SUCCESS(f"\n✓ Detected {len(trends)} trends\n")
        )
