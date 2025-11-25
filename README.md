# PublicWorks AI

> AI-powered platform for analyzing public contracts in Spain, detecting overpricing, risks, and corruption patterns.

## Features

- **Automated Data Collection**: Multi-source crawlers for PCSP, BOE, and regional platforms
- **ETL Pipeline**: Normalize and clean contract data from multiple sources
- **AI Risk Analysis**: 4 specialized models analyzing overpricing, corruption, delays, and providers
- **REST API**: 31 endpoints for comprehensive data access
- **Modern Dashboard**: Next.js frontend with real-time analytics and insights
- **100% Test Coverage**: Production-ready code with comprehensive test suites

## Architecture

```
dontfuckwithnews/
├── backend/
│   ├── apps/
│   │   ├── core/           # Base models and utilities
│   │   ├── contracts/      # Contract models, ETL, and API
│   │   ├── crawlers/       # Multi-source data crawlers
│   │   └── analytics/      # AI models and analytics
│   ├── config/             # Django settings
│   └── requirements/       # Python dependencies
└── frontend/
    ├── app/                # Next.js pages (Dashboard, Contracts, Providers, Alerts, Analytics)
    ├── components/         # Reusable React components
    └── lib/                # API client and utilities
```

## Tech Stack

### Backend
- **Django 5.0** - Core framework
- **PostgreSQL** - Primary database
- **Celery + Redis** - Async tasks
- **pytest** - Testing framework
- **Django REST Framework** - API layer

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Recharts** - Data visualization

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+

### Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements/local.txt

# Configure environment (create .env file with DB credentials)
cp .env.example .env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run tests
pytest --cov=apps

# Start development server
python manage.py runserver
```

Backend will be available at http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment (create .env.local with API URL)
echo "API_URL=http://localhost:8000/api/v1" > .env.local

# Start development server
npm run dev
```

Frontend will be available at http://localhost:3000

## Project Philosophy

- **Quality over Quantity** - Clean, maintainable code
- **Test-Driven** - Comprehensive test coverage
- **Documentation** - Effective, not excessive
- **Professional** - Production-ready from day one

## Usage

### Data Collection

Run crawlers to collect contract data:

```bash
# Run all registered crawlers
python manage.py run_crawlers

# Run specific crawler
python manage.py run_crawlers --crawler pcsp_crawler
```

### ETL Processing

Process raw data into normalized contracts:

```bash
# Process all pending raw data
python manage.py process_raw_data

# Process specific platform
python manage.py process_raw_data --platform PCSP
```

### Risk Analysis

Analyze contracts for risks and generate alerts:

```bash
# Analyze all contracts
python manage.py analyze_risk

# Analyze and generate alerts
python manage.py analyze_risk --generate-alerts

# Analyze specific contract
python manage.py analyze_risk --contract-id 123
```

### API Endpoints

Access the API at http://localhost:8000/api/v1/

Key endpoints:

**Contracts**
- `GET /contracts/` - List contracts with filters (search, region, type, risk, etc.)
- `GET /contracts/{id}/` - Contract details
- `POST /contracts/{id}/analyze/` - Trigger risk analysis
- `GET /contracts/stats/` - Contract statistics
- `GET /contracts/by_region/` - Group contracts by region
- `GET /contracts/by_type/` - Group contracts by type

**Providers**
- `GET /providers/` - List providers with filters
- `GET /providers/{id}/` - Provider details
- `GET /providers/{id}/contracts/` - Provider's contracts
- `GET /providers/{id}/alerts/` - Provider's alerts

**Alerts**
- `GET /providers/alerts/` - List all alerts
- `GET /providers/alerts/unresolved/` - Unresolved alerts
- `GET /providers/alerts/critical/` - Critical alerts

**Analytics**
- `GET /analytics/dashboard/` - Dashboard statistics
- `GET /analytics/regional_stats/` - Regional breakdown
- `GET /analytics/trends/` - Contract trends over time
- `GET /analytics/risk_distribution/` - Risk level distribution
- `GET /analytics/top_providers/` - Top providers by contracts or amount
- `GET /analytics/recent_high_risk/` - Recent high-risk contracts

## AI Models

### 1. Overpricing Detector (35% weight)
Compares contract budgets against:
- Regional averages
- Contracting authority patterns
- National benchmarks
- Similar contract types

Returns risk score and detailed evidence of pricing anomalies.

### 2. Corruption Risk Scorer (35% weight)
Analyzes corruption indicators:
- Provider market dominance (>30% of authority contracts)
- Rushed timelines (< 7 days from publication to deadline)
- Amendment patterns (multiple budget increases)
- Procedure type risks (negotiated vs competitive)
- Threshold gaming (contracts just below limits)

### 3. Delay Risk Predictor (20% weight)
Evaluates delivery risk based on:
- Historical provider delivery rates
- Provider track record with authority
- Contract complexity and size
- Timeline realism

### 4. Provider Analyzer (10% weight)
Assesses provider risk:
- Contract concentration (geographic, authority)
- Success rates and performance
- Pricing patterns vs market
- Alert history

**Overall Risk Score**: Weighted combination of all models (0-100)

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage report
pytest --cov=apps --cov-report=html

# Run specific app tests
pytest apps/contracts/tests/
pytest apps/crawlers/tests/
pytest apps/analytics/tests/

# Run specific test file
pytest apps/contracts/tests/test_models.py
```

Test coverage includes:
- Models and business logic
- API endpoints (100% coverage)
- Crawlers (fetch, parse, save)
- ETL normalizers
- AI risk models
- Management commands

### Code Quality

```bash
# Format code
black .

# Lint
flake8

# Type checking
mypy apps/

# Run all quality checks
black . && flake8 && mypy apps/ && pytest
```

## Frontend Pages

The Next.js frontend includes:

- **Dashboard** (`/`) - Overview statistics and recent high-risk contracts
- **Contracts** (`/contracts`) - Browse and filter contracts with search
- **Contract Detail** (`/contracts/[id]`) - Comprehensive contract analysis
- **Providers** (`/providers`) - Browse contractor profiles
- **Provider Detail** (`/providers/[id]`) - Provider analytics and contract history
- **Alerts** (`/alerts`) - System alerts for risks and anomalies
- **Analytics** (`/analytics`) - Trends, charts, and regional statistics

## License

Proprietary - All Rights Reserved
