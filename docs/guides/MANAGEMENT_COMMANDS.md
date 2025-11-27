# Management Commands

Django management commands for operating the PublicWorks AI system.

## Available Commands

### Data Collection

#### `run_crawlers`
Fetch new contract data from external sources.

```bash
# Run all crawlers
python manage.py run_crawlers

# Run specific crawler
python manage.py run_crawlers --only boe
python manage.py run_crawlers --only pcsp

# Run multiple crawlers
python manage.py run_crawlers --only boe,pcsp

# List all available crawlers
python manage.py run_crawlers --list
```

**Sources**:
- **BOE**: Spanish official state bulletin (Boletín Oficial del Estado)
- **PCSP**: Public procurement platform (Plataforma de Contratación del Sector Público)

**Output**: Creates `RawContractData` records in database.

---

### Data Processing

#### `process_raw_data`
Normalize raw contract data and extract providers.

```bash
# Process all unprocessed records
python manage.py process_raw_data

# Process specific source
python manage.py process_raw_data --source BOE
python manage.py process_raw_data --source PCSP

# Limit records processed
python manage.py process_raw_data --limit 50

# Reprocess already processed records
python manage.py process_raw_data --reprocess

# Extract and enrich provider data during processing
python manage.py process_raw_data --enrich-providers
```

**Features**:
- Validates contract data
- Creates normalized `Contract` records
- Extracts provider information (NIFs, company names)
- Optional integration with provider enrichment pipeline
- Reports success/failure for each record

**Output**:
- `Contract` records in database
- Automatic `Provider` record creation
- Progress output showing processed/failed counts

---

### Provider Management

#### `enrich_providers`
Enrich provider data with information from external APIs.

```bash
# Enrich all providers
python manage.py enrich_providers

# Enrich with verbose output
python manage.py enrich_providers --verbose

# Limit enrichment to N providers
python manage.py enrich_providers --limit 100

# Dry run (simulate without saving)
python manage.py enrich_providers --dry-run

# Enrich specific providers by ID
python manage.py enrich_providers --provider-ids 1,2,3

# Enrich flagged providers only
python manage.py enrich_providers --filter-flagged

# Enrich high-risk providers only
python manage.py enrich_providers --filter-high-risk
```

**Features**:
- Fetches company information from PCSP API
- Updates provider fields: website, industry, founding year, etc.
- Only updates empty fields (preserves existing data)
- Includes error handling and logging
- Optional dry-run mode to preview changes

**Output**:
- Updated `Provider` records with enriched data
- Progress and statistics report

---

#### `recalculate_provider_metrics`
Recalculate provider statistics based on awarded contracts.

```bash
# Recalculate all providers
python manage.py recalculate_provider_metrics

# Recalculate specific provider
python manage.py recalculate_provider_metrics --id 36
```

**Metrics Calculated**:
- `total_contracts`: Number of contracts won
- `total_awarded_amount`: Total value of won contracts
- `avg_contract_amount`: Average contract value
- `success_rate`: Success percentage (100% if has contracts)
- `first_contract_date`: Date of first contract
- `last_contract_date`: Date of most recent contract

**Use When**:
- After importing new contracts
- After modifying contract data
- On regular schedule (daily/weekly)

---

### Fetch Provider NIFs

#### `fetch_nif_data`
Extract company NIFs (tax IDs) from existing contracts.

```bash
# Extract from BOE/PCSP raw contracts
python manage.py fetch_nif_data --source contracts

# Extract from normalized contracts
python manage.py fetch_nif_data --source normalized

# Extract from both sources
python manage.py fetch_nif_data --source all

# Limit results
python manage.py fetch_nif_data --limit 50

# Update provider database with extracted NIFs
python manage.py fetch_nif_data --update-providers

# Verbose output
python manage.py fetch_nif_data --verbose
```

**Output**: Reports found NIFs and optionally creates/updates Provider records.

---

## Common Workflows

### Initial Setup
```bash
# 1. Fetch data from sources
python manage.py run_crawlers

# 2. Process and extract providers
python manage.py process_raw_data --enrich-providers

# 3. Recalculate provider metrics
python manage.py recalculate_provider_metrics

# System is now ready to use
```

### Daily Update
```bash
# Update with latest data
python manage.py run_crawlers --only boe

# Process new contracts
python manage.py process_raw_data

# Refresh provider metrics
python manage.py recalculate_provider_metrics
```

### Provider Enrichment
```bash
# Option 1: Enrich during contract processing
python manage.py process_raw_data --enrich-providers

# Option 2: Enrich existing providers separately
python manage.py enrich_providers --verbose --limit 100
```

### Data Quality Check
```bash
# Dry run to see what would change
python manage.py enrich_providers --dry-run

# Check provider metrics
python manage.py recalculate_provider_metrics --id 1
```

---

## Docker Usage

All commands can be run in Docker:

```bash
# Run command in backend container
docker-compose exec backend python manage.py run_crawlers

# Or with attached output
docker-compose exec -it backend python manage.py process_raw_data --enrich-providers
```

---

## Troubleshooting Commands

### Check Database Connection
```bash
python manage.py dbshell
# Type '\q' to exit
```

### Verify Data Integrity
```bash
python manage.py check
```

### View Recent Migrations
```bash
python manage.py showmigrations
```

### Create Backup
```bash
python manage.py dumpdata > backup.json
```

### Restore Backup
```bash
python manage.py loaddata backup.json
```

---

## Performance Tips

1. **Use `--limit` for large datasets** to avoid timeouts
2. **Run during off-peak hours** for enrichment operations
3. **Use `--dry-run` first** to preview changes
4. **Monitor logs** for errors: `docker-compose logs backend`
5. **Cache frequently accessed data** via Redis

---

## Scheduling Operations

For regular automated operations, set up cron jobs or Celery beat schedules:

```python
# In config/celery.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'crawl-daily': {
        'task': 'apps.crawlers.tasks.run_all_crawlers',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    'enrich-weekly': {
        'task': 'apps.providers.tasks.enrich_all_providers',
        'schedule': crontab(day_of_week=0, hour=2),  # Weekly Sunday 2am
    },
}
```

---

## See Also

- [Quick Start](01-QUICKSTART.md) - Getting started
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues
- [Architecture](../architecture/ARCHITECTURE.md) - System design
