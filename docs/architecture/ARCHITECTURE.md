# System Architecture

PublicWorks AI is a full-stack application for analyzing public procurement contracts in Spain.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js React)                 │
│  - Dashboard, Contracts, Providers, Analytics               │
│  - Real-time filtering and visualization                    │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST
┌────────────────────────▼────────────────────────────────────┐
│              Backend (Django + DRF)                         │
│  ├─ REST API (100+ endpoints)                               │
│  ├─ Business Logic                                          │
│  └─ Data Processing Pipeline                               │
└────────────────┬──────────────────────────┬─────────────────┘
                 │                          │
        ┌────────▼──────────┐      ┌──────▼────────────┐
        │   PostgreSQL DB   │      │  Redis Cache      │
        │                   │      │  & Task Queue     │
        │  - Contracts      │      │                   │
        │  - Providers      │      │  - Sessions       │
        │  - Analytics      │      │  - Rate Limit     │
        └───────────────────┘      └───────────────────┘
```

## Component Overview

### Frontend (`/frontend`)
- **Technology**: Next.js 14, React 18, TypeScript
- **Pages**:
  - Dashboard: Overview and KPIs
  - Contracts: List, filter, and search contracts
  - Providers: Provider analysis and company information
  - Analytics: Advanced risk and trend analysis
- **Components**:
  - Filters, Tables, Charts, Maps
  - Visualizations: Recharts, Leaflet
- **State Management**: React hooks, Context API

### Backend (`/backend`)
- **Framework**: Django 4.2 + Django REST Framework
- **Structure**:
  ```
  apps/
  ├── contracts/     # Contract models, views, serializers
  ├── providers/     # Provider enrichment and analysis
  ├── analytics/     # Risk scoring and AI analysis
  ├── crawlers/      # Data collection from external APIs
  └── core/          # Base models and utilities
  ```

### Data Flow

1. **Collection** (Crawlers)
   - BOE Crawler: Fetches from Spanish official bulletin
   - PCSP Crawler: Fetches from public procurement platform
   - Raw data stored in `RawContractData`

2. **Processing** (ETL Pipeline)
   - Normalizes contract data
   - Extracts provider information (NIFs, company names)
   - Creates `Contract` and `Provider` records
   - Pipeline: `process_raw_data` management command

3. **Enrichment**
   - Enriches providers with external API data
   - Fetches: website, industry, founding year, etc.
   - Uses PCSP API via `enrich_providers` command

4. **Analysis**
   - Risk scoring (corruption, delay, financial)
   - Alert generation for high-risk contracts
   - Analytics aggregation for dashboards

5. **Visualization**
   - REST API serves processed data
   - Frontend queries and displays
   - Real-time filtering and sorting

## Database Schema (Simplified)

### Core Tables

**contracts_contract**
- id, external_id (unique)
- title, description, status
- budget, awarded_amount
- publication_date, award_date, deadline_date
- risk_score (calculated)
- awarded_to (FK → providers_provider)
- source_platform (BOE, PCSP)

**providers_provider**
- id, tax_id (NIF) - unique
- name, legal_name
- industry, company_size, founded_year
- region, address, city, postal_code
- website, phone, email
- total_contracts, total_awarded_amount
- risk_score, is_flagged
- created_at, updated_at

**contracts_rawcontractdata**
- id, external_id, source_platform
- raw_data (JSON)
- is_processed, created_at

**analytics_provideralert**
- id, provider (FK)
- severity, alert_type, title, description
- is_resolved, created_at

**analytics_amendment**
- id, contract (FK)
- amendment_type, description
- previous_amount, new_amount
- amendment_date

## API Layers

### Serializers
- `ContractListSerializer`: Lightweight contract data
- `ContractDetailSerializer`: Full contract with amendments
- `ProviderListSerializer`: Summary provider data
- `ProviderDetailSerializer`: Full provider with metrics

### ViewSets
- `ContractViewSet`: CRUD + custom actions (stats, by_region, by_type)
- `ProviderViewSet`: CRUD + custom actions (contracts, alerts, by_region)
- `AnalyticsViewSet`: Read-only endpoints for analytics

### Filters
- `ContractFilterSet`: Search, region, risk, contract type, budget range
- `ProviderFilterSet`: Search, risk, industry, flagged status

## Management Commands

Core operations are exposed as management commands:

```bash
python manage.py run_crawlers              # Fetch new data
python manage.py process_raw_data          # Normalize contracts
python manage.py enrich_providers          # Enrich provider data
python manage.py recalculate_provider_metrics  # Update statistics
```

See [Management Commands Guide](../guides/MANAGEMENT_COMMANDS.md) for details.

## Security Considerations

- API endpoints use Django REST Framework permissions
- No authentication required for read operations (public data)
- Write operations require admin authentication
- Database credentials in environment variables
- CORS configured for frontend domain

## Performance Characteristics

- **API Response Time**: <100ms average (cached)
- **Database Queries**: Optimized with select_related, prefetch_related
- **Cache TTL**: 5 minutes for aggregated data
- **Pagination**: 20 items default, 100 max
- **Indexing**: Created on id, external_id, risk_score, source_platform

## Scalability Notes

- Stateless API design allows horizontal scaling
- Database queries use connection pooling
- Redis caching reduces database load
- Bulk operations optimized with bulk_create
- Async tasks via Celery for long-running operations

## Development Environment

Uses Docker Compose for consistency:
- `backend`: Django development server
- `db`: PostgreSQL database
- `redis`: Caching and task queue
- `celery`: Background job worker
- `celery-beat`: Scheduled tasks

See [Development Guide](../setup/DEVELOPMENT.md) for setup.

## Technology Choices Rationale

| Component | Choice | Reason |
|-----------|--------|--------|
| Database | PostgreSQL | Excellent for relational data, JSON fields for raw data |
| Cache | Redis | Fast, supports task queue, session store |
| Frontend | Next.js | Server-side rendering, good for SEO, TypeScript support |
| REST API | Django REST Framework | Mature, well-tested, excellent documentation |
| Task Queue | Celery | Distributed task processing for background jobs |

---

For detailed information on specific modules, see:
- [Contracts Module](../guides/CONTRACTS.md)
- [Providers Module](../guides/PROVIDERS.md)
- [Analytics Engine](../guides/ANALYTICS.md)
