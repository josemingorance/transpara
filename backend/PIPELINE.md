# Data Pipeline Guide

This document explains how to run the complete data pipeline: **Extraction → Normalization → Risk Analysis**.

## Quick Start

Run the entire pipeline with one command:

```bash
make pipeline-full
```

This will:
1. Extract raw data from all crawlers
2. Normalize raw data into standardized contracts
3. Run risk analysis on all contracts
4. Generate a complete report

## Pipeline Steps

### Step 1: Data Extraction (Crawlers)

Extract raw data from various sources into `RawContractData` table.

```bash
# Run all crawlers
make crawl

# Or use the advanced script
bash .scripts/pipeline.sh crawl

# Or use Django directly
python manage.py run_crawlers

# Run specific crawler
python manage.py run_crawlers --only boe
```

**Available Crawlers:**

#### BOE Crawler
- **Source:** Boletín Oficial del Estado (Spain's official gazette)
- **Format:** JSON API
- **Data:** Administrative publications, regulations, announcements
- **Contains:** No budget information
- **URL:** https://www.boe.es/datosabiertos/api/boe/sumario

#### PCSP Crawler
- **Source:** Plataforma de Contratación del Sector Público (Spain's public procurement)
- **Format:** ATOM/XML feeds (ZIP archives)
- **Data:** Real public contracts with complete financial details
- **Contains:** Budget, awards, providers, procedures, dates
- **Data Source:** https://contrataciondelestado.es/wps/portal/plataforma/datos_abiertos/
- **Documentation:** [OpenPLACSP v1.3 Manual (PDF)](https://contrataciondelestado.es/datosabiertos/DGPE_PLACSP_OpenPLACSP_v.1.3.pdf)

**Important Note about PCSP:**
PCSP does NOT have a REST JSON API. Data is distributed as:
- ZIP files containing ATOM/XML feeds
- Organized by year and month
- Automatically attempts to download from Datos Abiertos
- Falls back to sample data if unavailable
- Includes comprehensive procurement details (budgets, awards, providers, CPV codes)

### Step 2: Data Normalization

Convert raw data from multiple sources into standardized `Contract` records.

```bash
# Normalize all unprocessed raw data
make normalize

# Or use the advanced script
bash .scripts/pipeline.sh normalize

# Or use Django directly
python manage.py process_raw_data

# Process specific source
python manage.py process_raw_data --source BOE

# Reprocess already processed records
python manage.py process_raw_data --reprocess

# Limit to X records
python manage.py process_raw_data --limit 100
```

### Step 3: Risk Analysis

Run AI models to analyze contract risk factors.

```bash
# Analyze all unanalyzed contracts
make analyze

# Or use the advanced script
bash .scripts/pipeline.sh analyze

# Or use Django directly
python manage.py analyze_risk --contracts

# Generate alerts for high-risk items
python manage.py analyze_risk --contracts --generate-alerts

# Reanalyze already analyzed contracts
python manage.py analyze_risk --contracts --reanalyze

# Analyze providers instead
python manage.py analyze_risk --providers
```

### Step 4: Reporting

Generate a complete execution report with statistics.

```bash
# Generate report
make pipeline-report

# Or use the advanced script
bash .scripts/pipeline.sh report
```

## Complete Pipeline Commands

### Simple Commands (one per step)

```bash
make crawl       # Extract data
make normalize   # Normalize to contracts
make analyze     # Run risk analysis
make pipeline    # Run all three steps
```

### Advanced Commands (with reporting)

```bash
make pipeline-full          # Complete pipeline with report
make pipeline-crawl         # Crawlers only
make pipeline-normalize     # Normalize only
make pipeline-analyze       # Analyze only
make pipeline-report        # Generate report only
```

### Direct Script Usage

```bash
# Run complete pipeline
bash .scripts/pipeline.sh pipeline

# Run individual steps
bash .scripts/pipeline.sh crawl
bash .scripts/pipeline.sh normalize
bash .scripts/pipeline.sh analyze
bash .scripts/pipeline.sh report

# Get help
bash .scripts/pipeline.sh help
```

## AI Models for Risk Analysis

The risk analysis phase uses 4 AI models with the following weights:

| Model | Weight | What it detects |
|-------|--------|-----------------|
| **Overpricing Detector** | 35% | Price deviations from regional/historical/national averages |
| **Corruption Risk Scorer** | 35% | Provider dominance, rushed timelines, amendments, threshold gaming |
| **Delay Predictor** | 20% | Provider delay history, complexity, contract type patterns |
| **Financial Risk Analyzer** | 10% | Budget size, overruns, financial anomalies |

Risk scores are calculated as a weighted average of all 4 models.

## Risk Score Levels

- **MINIMAL** (0-20): Normal procurement process
- **LOW** (20-40): Standard oversight sufficient
- **MEDIUM** (40-60): Monitoring advised
- **HIGH** (60-75): Detailed review recommended
- **CRITICAL** (75-100): Immediate investigation required

## Output Examples

### Crawler Output
```
Running: boe...
  ✓ boe: 95 created, 0 updated (1.2s)
```

### Normalization Output
```
Processing 95 record(s)...
  ✓ BOE-A-2025-23915
  ✓ BOE-A-2025-23917
  ...
✓ Completed: 94 processed, 1 failed
```

### Risk Analysis Output
```
Analyzing 94 contract(s)...
  ✓ BOE-A-2025-23915: 8.0 (MINIMAL)
  ✓ BOE-A-2025-23917: 8.5 (MINIMAL)
  ⚠ CTR-2024-005: 55.8 (MEDIUM)
  ⚠ CTR-2024-001: 54.8 (MEDIUM)
```

### Report Output
```
============================================================
DATA PIPELINE EXECUTION REPORT
============================================================

┌─ RAW DATA EXTRACTION
│  Total Records: 95
│  Processed: 94
│  Failed: 1
│
├─ CONTRACT NORMALIZATION
│  Total Contracts: 94
│  By Source:
│    • BOE: 94
│
├─ RISK ANALYSIS
│  Analyzed: 94/94
│    MINIMAL: 94
│  Average Risk Score: 8.01/100
│
└─ PIPELINE STATUS
   ✓ Pipeline execution completed successfully
   ✓ 94 contracts in database
   ✓ 94 contracts analyzed
```

## Troubleshooting

### Issue: "Python not found" or "Django not found"

**Solution:** The script automatically detects and uses the virtual environment. Make sure it exists at:
- `.venv/` (local to backend)
- `../.venv/` (parent directory, shared with project root)

### Issue: Database connection error

**Solution:** Ensure Docker containers are running:
```bash
docker-compose up -d
```

And that `.env` has correct database settings.

### Issue: Crawler produces no data

**Solution:** Check that external APIs are accessible:
- BOE API: https://www.boe.es/datosabiertos/api/boe/sumario
- PCSP API: Check API endpoint configuration

### Issue: Risk analysis fails on some contracts

**Solution:** Some sources (like BOE) may not have budget information. This is expected and the risk analysis will adapt by skipping budget-dependent checks.

## Database Schema

### RawContractData
Stores unprocessed crawler output with source information.

```
- id
- source_platform (BOE, PCSP, etc.)
- external_id (unique per source)
- raw_data (JSONField)
- is_processed (True/False)
- processing_error (if any)
- contract (ForeignKey to Contract after processing)
```

### Contract
Normalized contract records with standardized fields.

```
- id
- external_id (unique)
- title
- description
- contract_type (WORKS, SERVICES, SUPPLIES, MIXED, OTHER)
- status (PUBLISHED, AWARDED, IN_PROGRESS, COMPLETED, CANCELLED)
- budget
- awarded_amount
- procedure_type (OPEN, RESTRICTED, NEGOTIATED, MINOR, COMPETITIVE_DIALOGUE)
- publication_date
- deadline_date
- award_date
- contracting_authority
- awarded_to (ForeignKey to Provider)
- source_platform
- source_url

# Risk Analysis Fields
- risk_score (0-100, overall)
- corruption_risk
- delay_risk
- financial_risk
- is_overpriced
- analyzed_at (timestamp)
```

## API Integration

After running the pipeline, contracts are available for API consumption with risk scores and detailed analysis results.

```bash
# View contracts via Django shell
python manage.py shell

from apps.contracts.models import Contract
contracts = Contract.objects.filter(risk_score__gte=60)  # High risk
```

## Performance Notes

Pipeline execution time depends on:
- Number of records to process
- API response times
- Database size

Typical times:
- Crawl: 1-5 seconds per source
- Normalize: 0.1-0.5 seconds per record
- Analyze: 0.3-1 second per contract

## Next Steps

After running the pipeline, you can:
1. Generate analytics reports
2. Create REST API endpoints to expose contract data
3. Build dashboards for risk visualization
4. Set up automated alerts for high-risk contracts
5. Implement historical tracking and trend analysis
