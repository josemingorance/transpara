# Quick Start Guide

Get PublicWorks AI running in 5 minutes.

## Prerequisites

- Docker & Docker Compose
- Git
- 2GB RAM minimum

## Installation (Docker)

```bash
# Clone repository
git clone <repo-url>
cd transpara

# Start all services
docker-compose up -d

# Wait for database to be ready
sleep 10

# Run migrations
docker-compose exec backend python manage.py migrate

# Import real data
docker-compose exec backend python manage.py run_crawlers

# Process contracts and extract providers
docker-compose exec backend python manage.py process_raw_data --enrich-providers

# Calculate provider metrics
docker-compose exec backend python manage.py recalculate_provider_metrics
```

## Access the Application

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/v1/
- **Django Admin**: http://localhost:8000/admin/

Default credentials:
- Username: `admin`
- Password: `admin`

## What's Loaded

After setup you'll have:
- **107 real contracts** from Spain's BOE (Boletín Oficial del Estado)
- **4 providers** automatically extracted
- **€19M** in procurement budget
- **Full analytics** on contract distribution

## Verify Installation

```bash
# Check backend health
curl http://localhost:8000/api/v1/contracts/

# Check API stats
curl http://localhost:8000/api/v1/analytics/dashboard/

# List crawlers
docker-compose exec backend python manage.py run_crawlers --list
```

## Common Operations

### View Contract Details
```
Frontend: http://localhost:3000/contracts
API: GET /api/v1/contracts/?search=keyword&high_risk=true
```

### View Provider Analysis
```
Frontend: http://localhost:3000/providers
API: GET /api/v1/providers/?region=Madrid
```

### Update Data
```bash
# Fetch new contracts
docker-compose exec backend python manage.py run_crawlers --only boe

# Process all unprocessed contracts
docker-compose exec backend python manage.py process_raw_data

# Enrich provider data from public APIs
docker-compose exec backend python manage.py enrich_providers
```

## Troubleshooting

**Port already in use?**
```bash
# Change ports in docker-compose.yml then:
docker-compose up -d
```

**Database connection error?**
```bash
# Ensure database is ready
docker-compose exec db pg_isready
```

**Migrations failed?**
```bash
# Check logs
docker-compose logs backend
```

See [Troubleshooting Guide](TROUBLESHOOTING.md) for more help.

## Next Steps

- Read [Architecture](../architecture/ARCHITECTURE.md) to understand the system
- Explore [API Documentation](../api/API.md) for endpoint details
- Check [Management Commands](MANAGEMENT_COMMANDS.md) for operations

---

**Time to setup**: ~2 minutes
**Data loading**: ~1 minute
**API ready**: Immediately after migrations
