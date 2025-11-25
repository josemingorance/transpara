# PublicWorks AI - System Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      DATA COLLECTION                        │
├─────────────────────────────────────────────────────────────┤
│  Crawlers (PCSP, BOE, Regions, Municipalities)            │
│  ↓ Fetch raw HTML/JSON/PDF                                 │
│  ↓ Store in RawContractData                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      ETL PIPELINE                           │
├─────────────────────────────────────────────────────────────┤
│  Normalizers (PCSP, BOE, etc.)                             │
│  ↓ Parse & validate data                                   │
│  ↓ Create Contract + Provider records                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      AI ENGINE                              │
├─────────────────────────────────────────────────────────────┤
│  Risk Analysis Models                                       │
│  ↓ Calculate risk scores                                   │
│  ↓ Detect anomalies                                        │
│  ↓ Generate alerts                                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      API LAYER                              │
├─────────────────────────────────────────────────────────────┤
│  REST API (Django REST Framework)                          │
│  ↓ Expose data endpoints                                   │
│  ↓ Filter, paginate, serialize                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND                               │
├─────────────────────────────────────────────────────────────┤
│  Next.js Dashboard                                          │
│  ↓ Visualize contracts                                     │
│  ↓ Display analytics                                       │
│  ↓ Manage alerts                                           │
└─────────────────────────────────────────────────────────────┘
```

## Detailed Component Architecture

### 1. Crawler Engine

```
BaseCrawler (Abstract)
  ├── HTMLCrawler
  │    └── PCSPCrawler
  │    └── BOECrawler (planned)
  │
  ├── JSONCrawler
  │    └── APIBasedCrawlers (planned)
  │
  └── PDFCrawler (planned)

Flow:
1. fetch_raw()    → Download data
2. parse()        → Extract structured data
3. save()         → Store in RawContractData
4. run_crawler()  → Orchestrate entire process

Features:
- Automatic retry on failure
- Rate limiting support
- Session management
- Error logging
- Metrics tracking
```

### 2. ETL Pipeline

```
BaseNormalizer (Abstract)
  ├── PCSPNormalizer
  ├── BOENormalizer
  └── RegionalNormalizers (planned)

Flow:
1. normalize()           → Transform raw data
2. _save_contract()      → Create/update Contract
3. _get_or_create_provider() → Handle providers
4. process_raw_record()  → Complete pipeline

Utilities:
- parse_date()          → Handle multiple date formats
- parse_money()         → Handle multiple currency formats
- normalize_contract_type()  → Standardize types
- normalize_status()    → Standardize statuses
```

### 3. Data Models

```
┌──────────────┐         ┌──────────────┐
│  Contract    │────────▶│  Provider    │
│              │         │              │
│ - budget     │         │ - tax_id     │
│ - risk_score │         │ - risk_score │
│ - status     │         │ - metrics    │
└──────────────┘         └──────────────┘
       │                        │
       │                        │
       ▼                        ▼
┌──────────────┐         ┌──────────────┐
│ Amendment    │         │ Alert        │
└──────────────┘         └──────────────┘

Relationships:
- Contract → Provider (many-to-one)
- Contract → Amendments (one-to-many)
- Provider → Alerts (one-to-many)
- Provider → Relationships (many-to-many)
```

### 4. AI Engine Architecture (Planned)

```
BaseAIModel (Abstract)
  ├── OverpricingDetector
  │    ├── MarketComparison
  │    ├── HistoricalAnalysis
  │    └── AnomalyDetection
  │
  ├── CorruptionRiskScorer
  │    ├── ProviderPatterns
  │    ├── TenderAnalysis
  │    └── NetworkDetection
  │
  ├── DelayPredictor
  │    ├── HistoricalData
  │    ├── ProviderTrack
  │    └── ComplexityFactors
  │
  └── ProviderAnalyzer
       ├── RelationshipMapper
       ├── BehaviorAnalysis
       └── ShellCompanyDetector

Flow:
1. Fetch contract/provider data
2. Run relevant AI models
3. Calculate aggregate risk score
4. Generate alerts if thresholds exceeded
5. Store results in database
```

### 5. API Architecture (Planned)

```
/api/v1/
  ├── /contracts/
  │    ├── GET  /                    List contracts
  │    ├── GET  /:id/                Contract detail
  │    ├── GET  /:id/amendments/     Amendments
  │    ├── POST /search/             Advanced search
  │    └── GET  /:id/risk-analysis/  Risk breakdown
  │
  ├── /providers/
  │    ├── GET  /                    List providers
  │    ├── GET  /:id/                Provider detail
  │    ├── GET  /:id/contracts/      Provider contracts
  │    ├── GET  /:id/alerts/         Provider alerts
  │    └── GET  /:id/network/        Relationship graph
  │
  └── /analytics/
       ├── GET  /dashboard/          Dashboard stats
       ├── GET  /trends/             Time series data
       ├── GET  /regions/            Regional comparisons
       └── GET  /alerts/             System alerts

Features:
- Pagination (PageNumberPagination)
- Filtering (django-filter)
- Ordering (OrderingFilter)
- Search (SearchFilter)
- Documentation (Swagger/ReDoc)
```

## Technology Stack

### Backend
```
Language:        Python 3.11+
Framework:       Django 5.0
API:            Django REST Framework 3.14
Database:        PostgreSQL 15
Cache:           Redis 7
Task Queue:      Celery 5.3
Web Scraping:    BeautifulSoup, Requests, Selenium
Testing:         pytest, pytest-django
Code Quality:    black, flake8, mypy
```

### Frontend (Planned)
```
Framework:       Next.js 14
Language:        TypeScript
Styling:         Tailwind CSS
Charts:          Recharts / ECharts
State:           React Context / Zustand
API Client:      Fetch API / Axios
```

### Infrastructure
```
Containers:      Docker, Docker Compose
Database:        PostgreSQL (AWS RDS in prod)
Cache/Queue:     Redis (AWS ElastiCache in prod)
Web Server:      Gunicorn + Nginx
Monitoring:      Sentry (optional)
Hosting:         AWS / DigitalOcean / Vercel
```

## Data Flow Example

### Complete Pipeline Example

```
1. CRAWLING
   ┌─────────────────────────────────────────────┐
   │ PCSPCrawler.run_crawler()                   │
   │ ↓ Fetch HTML from contrataciondelestado.es │
   │ ↓ Parse with BeautifulSoup                 │
   │ ↓ Extract contract data                    │
   │ ↓ Save to RawContractData                  │
   └─────────────────────────────────────────────┘

2. ETL
   ┌─────────────────────────────────────────────┐
   │ PCSPNormalizer.process_raw_record()         │
   │ ↓ Normalize dates (DD/MM/YYYY → date)      │
   │ ↓ Normalize money (1.234,56 € → Decimal)   │
   │ ↓ Normalize types (Obra → WORKS)           │
   │ ↓ Create/update Contract                   │
   │ ↓ Create/update Provider                   │
   └─────────────────────────────────────────────┘

3. AI ANALYSIS (planned)
   ┌─────────────────────────────────────────────┐
   │ RiskCalculator.analyze_contract()           │
   │ ↓ Compare price to market average          │
   │ ↓ Check provider history                   │
   │ ↓ Analyze tender patterns                  │
   │ ↓ Calculate risk scores                    │
   │ ↓ Generate alerts if needed                │
   └─────────────────────────────────────────────┘

4. API EXPOSURE (planned)
   ┌─────────────────────────────────────────────┐
   │ GET /api/v1/contracts/12345/                │
   │ ↓ Fetch contract from database             │
   │ ↓ Serialize with ContractSerializer        │
   │ ↓ Return JSON response                     │
   └─────────────────────────────────────────────┘

5. FRONTEND DISPLAY (planned)
   ┌─────────────────────────────────────────────┐
   │ Contract Detail Page                        │
   │ ↓ Fetch data from API                      │
   │ ↓ Display contract info                    │
   │ ↓ Show risk analysis                       │
   │ ↓ Render charts                            │
   └─────────────────────────────────────────────┘
```

## Database Schema

### Core Tables

```sql
-- Contracts
CREATE TABLE contracts_contract (
    id BIGSERIAL PRIMARY KEY,
    external_id VARCHAR(200) UNIQUE,
    title VARCHAR(500),
    contract_type VARCHAR(20),
    budget DECIMAL(15,2),
    risk_score DECIMAL(5,2),
    awarded_to_id BIGINT REFERENCES providers_provider,
    -- ... other fields
);

-- Providers
CREATE TABLE providers_provider (
    id BIGSERIAL PRIMARY KEY,
    tax_id VARCHAR(50) UNIQUE,
    name VARCHAR(300),
    total_contracts INTEGER,
    total_awarded_amount DECIMAL(15,2),
    risk_score DECIMAL(5,2),
    -- ... other fields
);

-- Raw Data
CREATE TABLE contracts_rawcontractdata (
    id BIGSERIAL PRIMARY KEY,
    source_platform VARCHAR(100),
    external_id VARCHAR(200),
    raw_data JSONB,
    is_processed BOOLEAN,
    contract_id BIGINT REFERENCES contracts_contract,
    -- ... other fields
);
```

### Key Indexes

```sql
CREATE INDEX idx_contract_risk ON contracts_contract(risk_score);
CREATE INDEX idx_contract_status ON contracts_contract(status);
CREATE INDEX idx_contract_region ON contracts_contract(region);
CREATE INDEX idx_provider_risk ON providers_provider(risk_score);
CREATE INDEX idx_raw_processed ON contracts_rawcontractdata(is_processed);
```

## Security Considerations

### Current Implementation
- ✅ Environment variable configuration
- ✅ Secret key management
- ✅ Database credentials isolation
- ✅ No hardcoded secrets

### Production Requirements
- 🔲 HTTPS/TLS everywhere
- 🔲 API authentication (JWT)
- 🔲 Rate limiting
- 🔲 CORS configuration
- 🔲 SQL injection protection (Django ORM)
- 🔲 XSS protection (Django templates)
- 🔲 CSRF tokens
- 🔲 Security headers

## Scalability Considerations

### Current Capacity
- Single server deployment
- Suitable for: 100k - 1M contracts
- Estimated: 10-100 concurrent users

### Scaling Strategies

**Horizontal Scaling**
```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Web 1   │     │ Web 2   │     │ Web N   │
└────┬────┘     └────┬────┘     └────┬────┘
     │               │               │
     └───────────────┴───────────────┘
                    │
            ┌───────┴────────┐
            │ Load Balancer  │
            └───────┬────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
    ┌────┴─────┐         ┌────┴─────┐
    │ Database │         │  Cache   │
    │ (Primary)│         │  (Redis) │
    └────┬─────┘         └──────────┘
         │
    ┌────┴─────┐
    │ Database │
    │(Replicas)│
    └──────────┘
```

**Celery Workers**
```
Multiple workers for different tasks:
- crawler_worker: Data collection
- etl_worker: Data processing
- ai_worker: Risk analysis
- export_worker: Report generation
```

---

**Design Principles Applied**:
- Separation of Concerns
- Single Responsibility
- Dependency Inversion
- Don't Repeat Yourself (DRY)
- Keep It Simple (KISS)
- You Aren't Gonna Need It (YAGNI)
