"""
Django management command to populate region data for contracts.

This command assigns Spanish autonomous communities to contracts randomly
to enable geographic visualization features.
"""
from random import choice
from django.core.management.base import BaseCommand
from apps.contracts.models import Contract

# Spanish autonomous communities with their provinces
SPANISH_REGIONS = {
    "Andalusía": ["Almería", "Cádiz", "Córdoba", "Granada", "Huelva", "Jaén", "Málaga", "Sevilla"],
    "Aragón": ["Huesca", "Teruel", "Zaragoza"],
    "Principado de Asturias": ["Asturias"],
    "Islas Baleares": ["Baleares"],
    "Canarias": ["Las Palmas", "Santa Cruz de Tenerife"],
    "Cantabria": ["Cantabria"],
    "Castilla y León": ["Ávila", "Burgos", "León", "Palencia", "Salamanca", "Segovia", "Soria", "Valladolid", "Zamora"],
    "Castilla-La Mancha": ["Albacete", "Ciudad Real", "Cuenca", "Guadalajara", "Toledo"],
    "Cataluña": ["Barcelona", "Gerona", "Lleida", "Tarragona"],
    "Comunidad Valenciana": ["Alicante", "Castellón", "Valencia"],
    "Extremadura": ["Badajoz", "Cáceres"],
    "Galicia": ["A Coruña", "Lugo", "Ourense", "Pontevedra"],
    "Comunidad de Madrid": ["Madrid"],
    "Región de Murcia": ["Murcia"],
    "Comunidad Foral de Navarra": ["Navarra"],
    "País Vasco": ["Álava", "Guipúzcoa", "Vizcaya"],
    "La Rioja": ["La Rioja"],
}

SPANISH_CITIES = {
    "Andalusía": ["Sevilla", "Córdoba", "Jaén", "Granada", "Málaga", "Almería", "Cádiz"],
    "Aragón": ["Zaragoza", "Huesca", "Teruel"],
    "Principado de Asturias": ["Oviedo", "Gijón", "Avilés"],
    "Islas Baleares": ["Palma", "Ibiza"],
    "Canarias": ["Las Palmas", "Santa Cruz de Tenerife"],
    "Cantabria": ["Santander"],
    "Castilla y León": ["Valladolid", "Burgos", "León", "Salamanca"],
    "Castilla-La Mancha": ["Toledo", "Cuenca", "Albacete"],
    "Cataluña": ["Barcelona", "Girona", "Lleida", "Tarragona"],
    "Comunidad Valenciana": ["Valencia", "Alicante", "Castellón"],
    "Extremadura": ["Badajoz", "Cáceres"],
    "Galicia": ["Santiago de Compostela", "A Coruña", "Lugo"],
    "Comunidad de Madrid": ["Madrid"],
    "Región de Murcia": ["Murcia"],
    "Comunidad Foral de Navarra": ["Pamplona"],
    "País Vasco": ["Bilbao", "Donostia", "Vitoria"],
    "La Rioja": ["Logroño"],
}


class Command(BaseCommand):
    """Command to populate region data for contracts."""

    help = "Populate region, province, and municipality data for contracts"

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Reset all region data before populating",
        )

    def handle(self, *args, **options):
        """Execute the command."""
        # Reset if requested
        if options["reset"]:
            Contract.objects.all().update(region="", province="", municipality="")
            self.stdout.write(self.style.WARNING("Reset all region data"))

        # Populate region data
        contracts = Contract.objects.all()
        total = contracts.count()
        updated = 0

        for i, contract in enumerate(contracts, 1):
            if not contract.region:
                # Pick a random region
                region = choice(list(SPANISH_REGIONS.keys()))
                province = choice(SPANISH_REGIONS[region])
                municipality = choice(SPANISH_CITIES.get(region, [province]))

                contract.region = region
                contract.province = province
                contract.municipality = municipality
                contract.save()
                updated += 1

            # Progress indicator every 10 contracts
            if i % 10 == 0:
                self.stdout.write(f"  Progress: {i}/{total} contracts")

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Updated {updated} contracts with region data\n"
            )
        )

        # Print summary
        from django.db.models import Count, Sum

        summary = (
            Contract.objects.exclude(region="")
            .values("region")
            .annotate(count=Count("id"), total_budget=Sum("budget"))
            .order_by("-count")
        )

        self.stdout.write("\n📍 REGIONAL SUMMARY:")
        for item in summary:
            self.stdout.write(
                f"  {item['region']}: {item['count']} contracts (€{item['total_budget'] or 0:,.0f})"
            )
