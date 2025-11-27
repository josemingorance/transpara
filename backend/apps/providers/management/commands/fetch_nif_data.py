"""
Fetch company NIFs and data from public Spanish sources.

Available sources:
1. PCSP API - Plataforma de Contratación del Sector Público (contracts data)
2. BOE API - Boletín Oficial del Estado (official notices)
3. datos.gob.es - Open data catalog
4. Extract from existing contracts in DB
"""

import requests
import json
from django.core.management.base import BaseCommand
from django.db.models import Count
from apps.providers.models import Provider
from apps.contracts.models import RawContractData, Contract

logger = __import__('logging').getLogger(__name__)


class NIFExtractor:
    """Extract NIFs from various sources."""

    @staticmethod
    def extract_from_contracts():
        """Extract NIFs from contracts already in database."""
        nifs_found = {}

        # From BOE contracts
        boe_contracts = RawContractData.objects.filter(source_platform='BOE')
        for contract in boe_contracts:
            try:
                data = json.loads(contract.raw_data)

                # Extract adjudicatario (awarded to)
                if 'adjudicatario' in data:
                    adj = data['adjudicatario']
                    nif = adj.get('nif') or adj.get('NIF')
                    nombre = adj.get('nombre') or adj.get('nombre_empresa')
                    if nif and nombre:
                        nifs_found[nif] = {
                            'name': nombre,
                            'source': 'BOE-adjudicatario',
                        }

                # Extract licitadores (bidders)
                if 'licitadores' in data:
                    for licitador in data.get('licitadores', []):
                        nif = licitador.get('nif') or licitador.get('NIF')
                        nombre = licitador.get('nombre') or licitador.get('nombre_empresa')
                        if nif and nombre:
                            if nif not in nifs_found:
                                nifs_found[nif] = {
                                    'name': nombre,
                                    'source': 'BOE-licitador',
                                }

                # Extract proveedores
                if 'proveedores' in data:
                    for proveedor in data.get('proveedores', []):
                        nif = proveedor.get('nif') or proveedor.get('NIF')
                        nombre = proveedor.get('nombre') or proveedor.get('nombre_empresa')
                        if nif and nombre:
                            if nif not in nifs_found:
                                nifs_found[nif] = {
                                    'name': nombre,
                                    'source': 'BOE-proveedor',
                                }
            except Exception as e:
                logger.warning(f"Error parsing BOE contract: {e}")
                continue

        # From PCSP contracts
        pcsp_contracts = RawContractData.objects.filter(source_platform='PCSP')
        for contract in pcsp_contracts:
            try:
                data = json.loads(contract.raw_data)

                if 'empresa' in data:
                    empresa = data['empresa']
                    nif = empresa.get('nif') or empresa.get('NIF')
                    nombre = empresa.get('nombre') or empresa.get('nombre_empresa')
                    if nif and nombre:
                        if nif not in nifs_found:
                            nifs_found[nif] = {
                                'name': nombre,
                                'source': 'PCSP',
                            }
            except Exception as e:
                logger.warning(f"Error parsing PCSP contract: {e}")
                continue

        return nifs_found

    @staticmethod
    def extract_from_normalized_contracts():
        """Extract NIFs from normalized contracts in database."""
        nifs_found = {}

        # Get awarded_to providers
        contracts = Contract.objects.filter(awarded_to__isnull=False).select_related('awarded_to')
        for contract in contracts:
            if contract.awarded_to:
                provider = contract.awarded_to
                nif = provider.tax_id
                if nif and provider.name:
                    if nif not in nifs_found:
                        nifs_found[nif] = {
                            'name': provider.name,
                            'source': 'Normalized-Contract',
                        }

        return nifs_found


class Command(BaseCommand):
    help = "Fetch company NIFs and data from public Spanish sources"

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            default='contracts',
            choices=['contracts', 'normalized', 'all'],
            help='Source to extract NIFs from'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of NIFs to process'
        )
        parser.add_argument(
            '--update-providers',
            action='store_true',
            help='Update/create providers with extracted NIFs'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output'
        )

    def handle(self, *args, **options):
        verbose = options.get('verbose', False)
        source = options.get('source', 'contracts')
        limit = options.get('limit')
        update_providers = options.get('update_providers', False)

        self.stdout.write(
            self.style.SUCCESS(f"\n{'='*70}")
        )
        self.stdout.write(
            self.style.SUCCESS("EXTRACTING NIFs FROM PUBLIC SOURCES")
        )
        self.stdout.write(
            self.style.SUCCESS(f"{'='*70}\n")
        )

        nifs_found = {}

        # Extract from contracts
        if source in ['contracts', 'all']:
            self.stdout.write("📋 Extracting from BOE/PCSP raw contract data...")
            raw_nifs = NIFExtractor.extract_from_contracts()
            nifs_found.update(raw_nifs)
            self.stdout.write(
                self.style.SUCCESS(f"  ✓ Found {len(raw_nifs)} unique NIFs\n")
            )

        # Extract from normalized contracts
        if source in ['normalized', 'all']:
            self.stdout.write("📊 Extracting from normalized contracts...")
            norm_nifs = NIFExtractor.extract_from_normalized_contracts()
            nifs_found.update(norm_nifs)
            self.stdout.write(
                self.style.SUCCESS(f"  ✓ Found {len(norm_nifs)} unique NIFs\n")
            )

        # Apply limit
        if limit:
            nifs_found = dict(list(nifs_found.items())[:limit])

        # Display results
        self.stdout.write(
            self.style.SUCCESS(f"\n📌 EXTRACTED {len(nifs_found)} UNIQUE NIFs:\n")
        )

        for i, (nif, data) in enumerate(sorted(nifs_found.items())[:20], 1):
            self.stdout.write(
                f"  {i:2d}. {nif:12s} → {data['name'][:50]:50s} ({data['source']})"
            )

        if len(nifs_found) > 20:
            self.stdout.write(f"  ... and {len(nifs_found) - 20} more")

        # Update providers if requested
        if update_providers:
            self.stdout.write(
                self.style.SUCCESS(f"\n\n{'='*70}")
            )
            self.stdout.write(
                self.style.SUCCESS("UPDATING PROVIDERS DATABASE")
            )
            self.stdout.write(
                self.style.SUCCESS(f"{'='*70}\n")
            )

            created = 0
            updated = 0
            skipped = 0

            for nif, data in nifs_found.items():
                try:
                    provider, is_new = Provider.objects.get_or_create(
                        tax_id=nif,
                        defaults={
                            'name': data['name'],
                            'legal_name': data['name'],
                        }
                    )

                    if is_new:
                        created += 1
                        if verbose:
                            self.stdout.write(
                                self.style.SUCCESS(f"  ✓ Created: {nif} - {data['name']}")
                            )
                    else:
                        if provider.name != data['name']:
                            provider.name = data['name']
                            provider.legal_name = data['name']
                            provider.save(update_fields=['name', 'legal_name'])
                            updated += 1
                            if verbose:
                                self.stdout.write(
                                    self.style.SUCCESS(f"  ✓ Updated: {nif} - {data['name']}")
                                )
                        else:
                            skipped += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"  ✗ Error with {nif}: {e}")
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"\n{'='*70}"
                )
            )
            self.stdout.write(
                f"\n  ✓ Created:   {created} providers\n"
                f"  ✓ Updated:   {updated} providers\n"
                f"  ⊘ Skipped:   {skipped} providers (no changes needed)\n"
            )
            self.stdout.write(
                self.style.SUCCESS(f"{'='*70}\n")
            )

        self.stdout.write(
            self.style.SUCCESS("✓ Extraction completed\n")
        )
