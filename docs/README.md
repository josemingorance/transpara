# PublicWorks AI - Documentation

Complete documentation for the PublicWorks AI system - a transparency platform for public procurement contracts in Spain.

## Quick Navigation

### Getting Started
- **[Quick Start](guides/01-QUICKSTART.md)** - Get the system running in 5 minutes
- **[Setup Guide](setup/SETUP.md)** - Detailed installation and configuration
- **[Docker Guide](setup/DOCKER.md)** - Running with Docker containers

### Architecture & Design
- **[System Architecture](architecture/ARCHITECTURE.md)** - Overall system design and components
- **[Project Structure](architecture/PROJECT_STRUCTURE.md)** - Directory and file organization
- **[Database Schema](architecture/DATABASE.md)** - Data model and relationships
- **[ETL Pipeline](architecture/ETL_PIPELINE.md)** - Data processing workflow

### Features & Implementation
- **[API Documentation](api/API.md)** - REST API endpoints and usage
- **[Provider Module](guides/PROVIDERS.md)** - Provider extraction and enrichment
- **[Contracts Module](guides/CONTRACTS.md)** - Contract processing and analysis
- **[Analytics & Risk](guides/ANALYTICS.md)** - Risk scoring and analytics engine
- **[Visualizations](guides/VISUALIZATIONS.md)** - Data visualization components

### Operations
- **[Management Commands](guides/MANAGEMENT_COMMANDS.md)** - CLI commands for operations
- **[Development Guide](setup/DEVELOPMENT.md)** - Setting up development environment
- **[Troubleshooting](guides/TROUBLESHOOTING.md)** - Common issues and solutions

### Technical Investigation & Research
- **[PCSP Data Understanding](UNDERSTANDING_PLACSP_DATA.md)** - Analysis of PLACSP structure and fields
- **[ATOM Structure Analysis](ATOM_STRUCTURE_ANALYSIS.md)** - ATOM feed parsing details
- **[Phase 1 Implementation](PHASE1_README.md)** - Crawler infrastructure and implementation
- **[Phase 1 Delivery Summary](PHASE1_DELIVERY_SUMMARY.md)** - What was delivered in Phase 1
- **[Data Availability Summary](DATA_AVAILABILITY_SUMMARY.md)** - Available data sources and coverage
- **[Quick Reference](QUICK_REFERENCE.md)** - Quick lookup for common tasks

## Project Status

**Phase 0 (Current): MVP Completion** ✅
- ✅ Contract crawling and normalization (PCSP)
- ✅ Provider extraction from contracts
- ✅ Provider enrichment with external APIs
- ✅ Risk scoring and analytics
- ✅ Frontend UI with filters and dashboards
- ✅ Code quality refactoring
- ✅ Simplified to PCSP-only implementation

**Phase 1 (Planned): Dashboard Enhancement**
- Provider geographic visualization
- Advanced risk analysis
- Temporal trend analysis
- Anomaly detection

## Technology Stack

### Backend
- **Framework**: Django 4.2 with Django REST Framework
- **Database**: PostgreSQL 15
- **Caching**: Redis 7
- **Task Queue**: Celery with Redis broker
- **Language**: Python 3.13

### Frontend
- **Framework**: Next.js 14 with React 18
- **Styling**: Tailwind CSS 3
- **Visualizations**: Recharts, Leaflet
- **Language**: TypeScript 5

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Database**: PostgreSQL 15-alpine
- **Cache**: Redis 7-alpine

## Key Metrics

- **107 Contracts** processed from real BOE data
- **4 Providers** automatically extracted and tracked
- **€19M** in total procurement budget
- **100+ API Endpoints** for data access
- **<100ms** average API response time

## Getting Help

1. Check the relevant guide from the navigation above
2. Review [Troubleshooting](guides/TROUBLESHOOTING.md) for common issues
3. Check [Management Commands](guides/MANAGEMENT_COMMANDS.md) for CLI operations

## File Organization

```
docs/
├── README.md (this file)
├── guides/
│   ├── 01-QUICKSTART.md
│   ├── PROVIDERS.md
│   ├── CONTRACTS.md
│   ├── ANALYTICS.md
│   ├── VISUALIZATIONS.md
│   ├── MANAGEMENT_COMMANDS.md
│   └── TROUBLESHOOTING.md
├── architecture/
│   ├── ARCHITECTURE.md
│   ├── PROJECT_STRUCTURE.md
│   ├── DATABASE.md
│   └── ETL_PIPELINE.md
├── api/
│   ├── API.md
│   └── ENDPOINTS.md
├── setup/
│   ├── SETUP.md
│   ├── DOCKER.md
│   └── DEVELOPMENT.md
├── UNDERSTANDING_PLACSP_DATA.md
├── ATOM_STRUCTURE_ANALYSIS.md
├── PHASE1_README.md
├── PHASE1_DELIVERY_SUMMARY.md
├── PHASE1_INTEGRATION_COMPLETE.md
├── DATA_AVAILABILITY_SUMMARY.md
├── QUICK_REFERENCE.md
├── DEBUG_FINDINGS.md
├── INVESTIGATION_SUMMARY.md
├── INVESTIGATION_COMPLETE.md
└── REFACTORING_COMPLETE.md
```

## License

Proprietary - All rights reserved

## Contributing

For development guidelines, see [Development Guide](setup/DEVELOPMENT.md).

---

**Last Updated**: November 2025
**Version**: 1.0.0 (Phase 0 Complete)
