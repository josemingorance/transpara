# Provider Enrichment - Quick Reference

## One-Liner Commands

```bash
# All providers
docker-compose exec backend python manage.py enrich_providers

# Test without saving (safe)
docker-compose exec backend python manage.py enrich_providers --dry-run

# With progress
docker-compose exec backend python manage.py enrich_providers --verbose

# First 50 providers
docker-compose exec backend python manage.py enrich_providers --limit 50

# Only flagged providers
docker-compose exec backend python manage.py enrich_providers --filter-flagged

# Only high-risk (risk > 70)
docker-compose exec backend python manage.py enrich_providers --filter-high-risk

# Madrid region only
docker-compose exec backend python manage.py enrich_providers --filter-region Madrid

# Cataluña region only
docker-compose exec backend python manage.py enrich_providers --filter-region Cataluña
```

## Common Combinations

### Test First, Run After
```bash
# 1. Dry-run to preview
docker-compose exec backend python manage.py enrich_providers --limit 20 --dry-run --verbose

# 2. If good, run for real
docker-compose exec backend python manage.py enrich_providers --limit 20
```

### Enrich High-Risk Providers
```bash
docker-compose exec backend python manage.py enrich_providers \
  --filter-high-risk \
  --verbose
```

### Region + Risk Targeting
```bash
docker-compose exec backend python manage.py enrich_providers \
  --filter-region Cataluña \
  --filter-high-risk \
  --limit 100
```

### Process Flagged Providers (Safe)
```bash
docker-compose exec backend python manage.py enrich_providers \
  --filter-flagged \
  --dry-run \
  --verbose
```

## What Gets Enriched

| Field | Source | Example |
|-------|--------|---------|
| Website | PCSP | https://example.com |
| Industry | PCSP | Construcción |
| Founded Year | PCSP | 2015 |
| Email | PCSP | info@example.com |
| Phone | PCSP | +34 91 123 4567 |
| Company Size | PCSP | Pequeña |
| Legal Name | PCSP | Acme Corp S.L. |

## Output Interpretation

```
Total processed: 50          ← Number of providers processed
Successfully enriched: 30    ← Providers with at least 1 new field

  • Websites: 15             ← Providers that got a website
  • Industries: 22           ← Providers that got an industry
  • Founding years: 8        ← Providers that got a founding year
  • Email addresses: 14      ← Providers that got an email
  • Phone numbers: 10        ← Providers that got a phone

Errors: 0                    ← API errors or processing failures
```

Success Rate = (Successfully enriched / Total processed) × 100%

## Safety Features

### Dry-Run Mode
```bash
# Simulates all operations without saving
--dry-run
```

- Shows what would be updated
- No database changes
- Safe to test

### Non-Destructive Updates
- Only fills **empty** fields
- Never overwrites existing data
- Preserves manual edits

### Verbose Logging
```bash
# Shows detailed progress
--verbose
```

- Logs each update
- Shows errors with details
- Helps troubleshoot

## Filter Options

| Option | Example | Effect |
|--------|---------|--------|
| `--limit N` | `--limit 50` | Process first 50 |
| `--filter-region STR` | `--filter-region Madrid` | Only this region |
| `--filter-flagged` | (no value) | Only flagged providers |
| `--filter-high-risk` | (no value) | Only risk > 70 |

## Environment

```bash
# Via Docker (recommended)
docker-compose exec backend python manage.py enrich_providers

# Via local Python (if running locally)
cd backend
source venv/bin/activate
python manage.py enrich_providers
```

## Performance Tips

1. **Start small**: Use `--limit 20` first
2. **Test first**: Always use `--dry-run` before real run
3. **Filter**: Use filters to target specific providers
4. **Monitor**: Use `--verbose` to see progress
5. **Schedule**: Run during off-peak hours

## Common Scenarios

### Scenario 1: Quick Test
```bash
# 5 providers, dry-run, see details
docker-compose exec backend python manage.py enrich_providers \
  --limit 5 \
  --dry-run \
  --verbose
```

### Scenario 2: Enrich All
```bash
# All providers, get full summary
docker-compose exec backend python manage.py enrich_providers
```

### Scenario 3: Fix Flagged
```bash
# Enrich only flagged, with details
docker-compose exec backend python manage.py enrich_providers \
  --filter-flagged \
  --verbose
```

### Scenario 4: Regional Focus
```bash
# All of Madrid, first batch
docker-compose exec backend python manage.py enrich_providers \
  --filter-region Madrid \
  --limit 100 \
  --verbose
```

## Help & Documentation

```bash
# Show all options
docker-compose exec backend python manage.py enrich_providers --help

# Full guide
cat backend/PROVIDER_ENRICHMENT_GUIDE.md

# Implementation details
cat PROVIDER_ENRICHMENT_SUMMARY.md
```

## Status Check

```bash
# Count providers by region
docker-compose exec backend python manage.py shell << 'PYTHON'
from apps.providers.models import Provider
Provider.objects.values('region').annotate(count=Count('id'))
PYTHON

# Find providers without websites
docker-compose exec backend python manage.py shell << 'PYTHON'
from apps.providers.models import Provider
Provider.objects.filter(website='').count()
PYTHON
```

## Troubleshooting

### Command not found
```bash
# Ensure you're in the right directory
cd /path/to/transpara
docker-compose exec backend python manage.py enrich_providers --help
```

### Database connection error
```bash
# Check if Docker containers are running
docker-compose ps

# If not, start them
docker-compose up -d
```

### No providers found
```bash
# Check your filter
docker-compose exec backend python manage.py shell << 'PYTHON'
from apps.providers.models import Provider
print(f"Total providers: {Provider.objects.count()}")
PYTHON
```

### API timeout
```bash
# Try with smaller batch
docker-compose exec backend python manage.py enrich_providers \
  --limit 10 \
  --verbose
```

## Quick Stats

- **Enrichment Rate**: ~60% (depends on data quality in PCSP)
- **API Timeout**: 10 seconds per request
- **Processing Speed**: ~5-10 seconds per provider
- **Memory Usage**: ~10MB for batch of 100

## Next Steps

1. Read full guide: `PROVIDER_ENRICHMENT_GUIDE.md`
2. Test with dry-run: `--dry-run --limit 10`
3. Enrich your providers: Run the command
4. Monitor results: Use `--verbose`
5. Schedule regular runs: Setup cron or Celery task

---

**For complete documentation, see `PROVIDER_ENRICHMENT_GUIDE.md`**
