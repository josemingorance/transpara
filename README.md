# PublicWorks AI

**Transparency Platform for Public Procurement Contracts in Spain**

🔗 **Full documentation has been moved to `/docs` folder**

## Quick Links

- **📖 [Complete Documentation](./docs/README.md)** - Start here
- **🚀 [Quick Start (5 mins)](./docs/guides/01-QUICKSTART.md)** - Get running immediately
- **🏗️ [System Architecture](./docs/architecture/ARCHITECTURE.md)** - Understand the system
- **📋 [Management Commands](./docs/guides/MANAGEMENT_COMMANDS.md)** - CLI operations
- **✅ [Refactoring Summary](./docs/REFACTORING_COMPLETE.md)** - Code quality details

## What is PublicWorks AI?

A full-stack transparency platform that analyzes public procurement contracts from Spain, extracting provider information, calculating risk scores, and providing analytics dashboards.

## Current Status

✅ **Phase 0: MVP Complete**
- 107 real contracts from BOE (Boletín Oficial del Estado)
- 4 providers automatically extracted and tracked
- €19M in total procurement budget
- Risk scoring and analytics engine
- Frontend dashboard with filters and visualizations

## Technology Stack

- **Backend**: Django 4.2 + Django REST Framework + PostgreSQL
- **Frontend**: Next.js 14 + React 18 + TypeScript + Tailwind CSS
- **Infrastructure**: Docker Compose with PostgreSQL + Redis
- **Visualizations**: Recharts + Leaflet

## Getting Started

```bash
# See Quick Start guide
cat docs/guides/01-QUICKSTART.md

# Or with Docker:
docker-compose up -d
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py run_crawlers
docker-compose exec backend python manage.py process_raw_data --enrich-providers
```

Access at:
- Frontend: http://localhost:3000
- API: http://localhost:8000/api/v1/
- Admin: http://localhost:8000/admin/

## Key Features

✅ **Real Data** - Contracts from official Spanish sources (BOE, PCSP)
✅ **Provider Extraction** - Automatic NIF and company extraction
✅ **Risk Scoring** - AI-based corruption, delay, and financial risk analysis
✅ **Analytics** - Contract distribution, regional analysis, trends
✅ **REST API** - 100+ endpoints for programmatic access
✅ **Responsive UI** - Modern frontend with filters and visualizations
✅ **Production Ready** - Clean code, enterprise standards, well documented

## License

Proprietary - All rights reserved

---

**Last Updated**: November 27, 2025 (Phase 0 Complete - Code Quality Refactoring)

**👉 Start with documentation**: [`docs/README.md`](./docs/README.md)
