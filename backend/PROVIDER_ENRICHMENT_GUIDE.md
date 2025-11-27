# Provider Data Enrichment Guide

## Overview

The Provider Enrichment system automatically enriches provider data from external sources, including:
- **PCSP** (Plataforma de Contratación del Sector Público) - Official Spanish public procurement platform
- **BOE** (Boletín Oficial del Estado) - Official Government Bulletin
- Additional sources (Linked Data, company registries)

### Data Enriched

- **Website**: Company website URL
- **Industry/Sector**: Business sector classification
- **Founding Year**: Company establishment date
- **Email Address**: Contact email
- **Phone Number**: Contact phone
- **Company Size**: Employee count or size classification
- **Legal Name**: Official company legal name

## Quick Start

### Basic Enrichment

Enrich all providers:
```bash
python manage.py enrich_providers
```

Enrich with progress output:
```bash
python manage.py enrich_providers --verbose
```

### Filtering Options

Enrich only a subset of providers:

```bash
# Limit to 50 providers
python manage.py enrich_providers --limit 50

# Only flagged providers
python manage.py enrich_providers --filter-flagged

# Only high-risk providers (risk_score > 70)
python manage.py enrich_providers --filter-high-risk

# Only providers from a specific region
python manage.py enrich_providers --filter-region Cataluña

# Combine filters
python manage.py enrich_providers --limit 100 --filter-region Madrid --filter-flagged
```

### Testing & Safety

Preview changes without saving:
```bash
python manage.py enrich_providers --dry-run
```

Dry-run with verbose output:
```bash
python manage.py enrich_providers --dry-run --verbose --limit 10
```

## Architecture

### Module Structure

```
backend/apps/providers/
├── enrichment.py              # API enricher classes
│   ├── APIEnricher           # Base class
│   ├── PCSPEnricher          # PCSP API integration
│   ├── BOEEnricher           # BOE API integration
│   ├── LinkedDataEnricher    # Linked Data sources
│   └── EnrichmentPipeline    # Orchestrator
│
└── management/commands/
    └── enrich_providers.py   # Django management command
        ├── ProviderBatchEnricher  # Batch processing
        └── Command                 # CLI interface
```

### Enrichment Pipeline

```
Provider (tax_id, name)
    ↓
EnrichmentPipeline
    ├─→ PCSPEnricher (Try NIF search)
    │    ├─ Search by tax ID
    │    └─ Fall back to name search
    ├─→ LinkedDataEnricher (Future)
    └─→ BOEEnricher (Future)
    ↓
Enriched Data
    ├─ website
    ├─ industry
    ├─ founded_year
    ├─ email
    └─ phone
    ↓
Provider Model (Save if not empty)
```

## API Details

### PCSP Enricher

Queries the official PCSP REST API:

```python
from apps.providers.enrichment import PCSPEnricher

enricher = PCSPEnricher(verbose=True)

# Search by tax ID (NIF/CIF)
result = enricher.search_provider(
    tax_id="A28001389",
    company_name="Example Corp"
)

# Returns dict with:
# {
#   "found": bool,
#   "source": "pcsp",
#   "website": str,
#   "industry": str,
#   "founded_year": int,
#   "email": str,
#   "phone": str,
#   ...
# }
```

### Enrichment Pipeline

Automatically tries multiple sources in priority order:

```python
from apps.providers.enrichment import EnrichmentPipeline

pipeline = EnrichmentPipeline(verbose=True)

enriched = pipeline.enrich(
    tax_id="A28001389",
    company_name="Example Corp"
)

if enriched.get("found"):
    print(f"Website: {enriched.get('website')}")
    print(f"Industry: {enriched.get('industry')}")
```

### Batch Enricher

Process multiple providers efficiently:

```python
from apps.providers.management.commands.enrich_providers import ProviderBatchEnricher
from apps.providers.models import Provider

enricher = ProviderBatchEnricher(verbose=True, dry_run=False)

providers = Provider.objects.all()[:100]
stats = enricher.enrich_batch(list(providers))

print(f"Enriched: {stats['enriched']}")
print(f"With websites: {stats['with_website']}")
```

## Usage Examples

### Example 1: Enrich High-Risk Providers

```bash
python manage.py enrich_providers \
  --filter-high-risk \
  --verbose \
  --limit 50
```

Output:
```
[DRY RUN] Enriching 12 provider(s)...
  Querying: PCSP, BOE, and other external data sources

===========================================================================
ENRICHMENT SUMMARY
===========================================================================

  Total processed:        12
  Successfully enriched:  8 (66.7%)

  Data added:
    • Websites:           6
    • Industries:         7
    • Founding years:     3
    • Email addresses:    4
    • Phone numbers:      2

  Errors:                 0
===========================================================================
```

### Example 2: Test with Dry-Run

```bash
python manage.py enrich_providers \
  --limit 10 \
  --dry-run \
  --verbose
```

No providers are modified, perfect for testing.

### Example 3: Enrich Specific Region

```bash
python manage.py enrich_providers \
  --filter-region "Madrid" \
  --verbose
```

### Example 4: Integrate in Celery Task

```python
# apps/providers/tasks.py
from celery import shared_task
from django.core.management import call_command

@shared_task
def enrich_providers_task(limit=None, region=None):
    """Async task to enrich providers."""
    args = []
    kwargs = {"verbosity": 1}

    if limit:
        kwargs["limit"] = limit
    if region:
        kwargs["filter_region"] = region

    call_command("enrich_providers", **kwargs)
```

Then call from Django shell or API:
```python
from apps.providers.tasks import enrich_providers_task
enrich_providers_task.delay(limit=100, region="Cataluña")
```

## Performance Notes

### Timeout and Rate Limiting

- **API Timeout**: 10 seconds per request
- **Retry Logic**: 2 retries on failure
- **Rate Limiting**: Respects API rate limits with backoff

### Optimization Tips

1. **Process in batches**: Use `--limit` to process in chunks
2. **Filter first**: Use filters to target providers needing enrichment
3. **Parallel processing**: Run multiple commands on different regions
4. **Schedule offline**: Run during low-traffic periods

### Database Impact

- **Selective updates**: Only updates empty fields (no overwrites)
- **Efficient queries**: Single `update_fields` call per provider
- **Index usage**: Queries use indexed fields (tax_id, region, risk_score)

## Troubleshooting

### Issue: "No providers found matching criteria"

Check your filter syntax:
```bash
# Wrong
python manage.py enrich_providers --filter-region Cat

# Right
python manage.py enrich_providers --filter-region Cataluña
```

### Issue: API Timeouts

PCSP API might be slow. Try:
- Reduce batch size: `--limit 10`
- Try specific region: `--filter-region Madrid`
- Run during off-peak hours

### Issue: No Data Enriched

This is normal! Enrichment depends on:
1. PCSP API having data for the company
2. Matching by tax ID (NIF/CIF)
3. Data quality in source systems

Check with `--verbose` to see search attempts:
```bash
python manage.py enrich_providers --limit 5 --verbose --dry-run
```

## Future Enhancements

### Planned Features

1. **BOE Search**: Extract company info from official notices
2. **Linked Data**: Query DBpedia, Wikidata, SPARQL endpoints
3. **Company Registries**: Integration with Mercantil Registry
4. **Historical Tracking**: Track enrichment changes over time
5. **Scoring**: Rank enrichment quality/completeness
6. **Webhooks**: Real-time enrichment on provider creation

### Configuration

Future versions will support:
```python
# settings.py
ENRICHMENT_CONFIG = {
    "pcsp": {
        "enabled": True,
        "timeout": 10,
        "retries": 2,
    },
    "boe": {
        "enabled": False,  # Not yet
    },
    "linked_data": {
        "enabled": False,  # Not yet
    }
}
```

## API Endpoints Reference

### PCSP API

- **Base URL**: `https://contrataciondelsectorpublico.gob.es/wlpl/rest`
- **Endpoint**: `/empresas/search`
- **Query**: `nif:A28001389` or `nombre:Company Name`
- **Response**: JSON with company details

### BOE API

- **Base URL**: `https://www.boe.es`
- **Status**: Documentation in progress
- **Usage**: Future implementation

## Integration Examples

### Django Shell

```python
python manage.py shell

from apps.providers.enrichment import EnrichmentPipeline
from apps.providers.models import Provider

pipeline = EnrichmentPipeline(verbose=True)

# Get a provider
provider = Provider.objects.first()

# Enrich it
enriched = pipeline.enrich(provider.tax_id, provider.name)

# Update if found
if enriched.get("found"):
    if enriched.get("website"):
        provider.website = enriched["website"]
    if enriched.get("industry"):
        provider.industry = enriched["industry"]
    if enriched.get("founded_year"):
        provider.founded_year = enriched["founded_year"]

    provider.save()
    print(f"✓ Updated: {provider.name}")
```

### REST API Integration

Future API endpoint:
```
POST /api/v1/providers/enrich/
{
  "limit": 50,
  "filter_region": "Madrid",
  "dry_run": false
}
```

## Contributing

To add new enrichment sources:

1. Create enricher class inheriting from `APIEnricher`
2. Implement `search_provider(tax_id, name)` method
3. Return dict with `found: bool` and extracted fields
4. Add to `EnrichmentPipeline.enrichers` list

Example:
```python
class MyEnricher(APIEnricher):
    def search_provider(self, tax_id, company_name):
        # Implementation
        return {"found": True, "website": "..."}
```

## Support & Documentation

- **Full API Reference**: See `enrichment.py` docstrings
- **Management Command**: `python manage.py enrich_providers --help`
- **Tests**: `backend/apps/providers/tests/test_enrichment.py`
- **Issues**: Report in GitHub issues with `enhancement-providers` tag

---

**Version**: 1.0
**Last Updated**: 2025-11-26
**Status**: Production Ready
