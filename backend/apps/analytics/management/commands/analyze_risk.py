"""
Django management command to analyze contract and provider risk.

Usage:
    python manage.py analyze_risk                        # Analyze all unanalyzed
    python manage.py analyze_risk --contracts            # Only contracts
    python manage.py analyze_risk --providers            # Only providers
    python manage.py analyze_risk --limit 100            # Limit number
    python manage.py analyze_risk --reanalyze            # Reanalyze all
    python manage.py analyze_risk --generate-alerts      # Create alerts
"""
from django.core.management.base import BaseCommand

from apps.analytics.services.alert_generator import AlertGenerator
from apps.analytics.services.risk_calculator import RiskCalculator
from apps.contracts.models import Contract
from apps.providers.models import Provider


class Command(BaseCommand):
    """Command to analyze risk for contracts and providers."""

    help = "Analyze risk scores using AI models"

    def add_arguments(self, parser) -> None:
        """Add command arguments."""
        parser.add_argument(
            "--contracts",
            action="store_true",
            help="Analyze contracts only",
        )
        parser.add_argument(
            "--providers",
            action="store_true",
            help="Analyze providers only",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Maximum number of records to analyze",
        )
        parser.add_argument(
            "--reanalyze",
            action="store_true",
            help="Reanalyze already analyzed records",
        )
        parser.add_argument(
            "--generate-alerts",
            action="store_true",
            help="Generate alerts for high-risk items",
        )

    def handle(self, *args, **options) -> None:
        """Execute the command."""
        self.calculator = RiskCalculator()
        self.alert_generator = AlertGenerator() if options["generate_alerts"] else None

        # Determine what to analyze
        analyze_contracts = options["contracts"] or not options["providers"]
        analyze_providers = options["providers"] or not options["contracts"]

        if analyze_contracts:
            self._analyze_contracts(options)

        if analyze_providers:
            self._analyze_providers(options)

        self.stdout.write(self.style.SUCCESS("\n✓ Analysis completed\n"))

    def _analyze_contracts(self, options: dict) -> None:
        """Analyze contracts."""
        # Build queryset
        queryset = Contract.objects.filter(status__in=["PUBLISHED", "AWARDED", "IN_PROGRESS"])

        if not options["reanalyze"]:
            queryset = queryset.filter(analyzed_at__isnull=True)

        if options["limit"]:
            queryset = queryset[: options["limit"]]

        total = queryset.count()

        if total == 0:
            self.stdout.write(self.style.WARNING("No contracts to analyze"))
            return

        self.stdout.write(self.style.SUCCESS(f"\nAnalyzing {total} contract(s)...\n"))

        analyzed = 0
        failed = 0
        high_risk = 0

        for contract in queryset:
            try:
                # Analyze contract
                analysis = self.calculator.analyze_contract(contract)

                analyzed += 1

                # Display result
                risk_score = analysis["overall"]["score"]
                risk_level = analysis["overall"]["level"]

                if risk_level in ["HIGH", "CRITICAL"]:
                    high_risk += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ {contract.external_id}: {risk_score:.1f} ({risk_level})"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ {contract.external_id}: {risk_score:.1f} ({risk_level})"
                        )
                    )

                # Generate alerts if requested
                if self.alert_generator and contract.awarded_to:
                    alerts = self.alert_generator.generate_contract_alerts(contract, analysis)
                    if alerts:
                        self.stdout.write(f"    → Generated {len(alerts)} alert(s)")

            except Exception as e:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(f"  ✗ {contract.external_id}: {e}")
                )

        # Summary
        self.stdout.write(
            f"\nContracts: {analyzed} analyzed, {failed} failed, {high_risk} high-risk"
        )

    def _analyze_providers(self, options: dict) -> None:
        """Analyze providers."""
        # Build queryset
        queryset = Provider.objects.filter(total_contracts__gt=0)

        if not options["reanalyze"]:
            queryset = queryset.filter(risk_score__isnull=True)

        if options["limit"]:
            queryset = queryset[: options["limit"]]

        total = queryset.count()

        if total == 0:
            self.stdout.write(self.style.WARNING("No providers to analyze"))
            return

        self.stdout.write(self.style.SUCCESS(f"\nAnalyzing {total} provider(s)...\n"))

        analyzed = 0
        failed = 0
        high_risk = 0

        for provider in queryset:
            try:
                # Analyze provider
                analysis = self.calculator.analyze_provider(provider)

                analyzed += 1

                # Display result
                risk_score = analysis["score"]

                if risk_score >= 60:
                    high_risk += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ {provider.name}: {risk_score:.1f} (HIGH RISK)"
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ {provider.name}: {risk_score:.1f}")
                    )

                # Generate alerts if requested
                if self.alert_generator:
                    alerts = self.alert_generator.generate_provider_alerts(provider, analysis)
                    if alerts:
                        self.stdout.write(f"    → Generated {len(alerts)} alert(s)")

            except Exception as e:
                failed += 1
                self.stdout.write(self.style.ERROR(f"  ✗ {provider.name}: {e}"))

        # Summary
        self.stdout.write(
            f"\nProviders: {analyzed} analyzed, {failed} failed, {high_risk} high-risk"
        )
