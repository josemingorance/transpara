# Docker Setup Guide

## Quick Start with Docker

The easiest way to get PublicWorks AI running is with Docker Compose.

### Prerequisites

- Docker Desktop installed
- Docker Compose installed (included with Docker Desktop)

### Start All Services

```bash
# Start all services
docker-compose up

# Or in detached mode
docker-compose up -d
```

This will start:
- PostgreSQL (port 5432)
- Redis (port 6379)
- Django Backend (port 8000)
- Celery Worker
- Celery Beat

### Initial Setup

```bash
# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Run tests
docker-compose exec backend pytest
```

### Access the Application

- **Admin**: http://localhost:8000/admin
- **API Docs**: http://localhost:8000/api/docs/
- **API Schema**: http://localhost:8000/api/schema/

### Common Commands

```bash
# View logs
docker-compose logs -f backend

# Run crawlers
docker-compose exec backend python manage.py run_crawlers

# Process raw data
docker-compose exec backend python manage.py process_raw_data

# Django shell
docker-compose exec backend python manage.py shell

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### Development Workflow

The backend directory is mounted as a volume, so changes are reflected immediately:

1. Edit code in `backend/`
2. Django auto-reloads
3. Tests run with `docker-compose exec backend pytest`

### Database Access

```bash
# PostgreSQL CLI
docker-compose exec db psql -U publicworks -d publicworks_db

# Or from host (if psql installed)
psql -h localhost -U publicworks -d publicworks_db
```

### Redis Access

```bash
# Redis CLI
docker-compose exec redis redis-cli

# Check keys
docker-compose exec redis redis-cli KEYS '*'
```

### Troubleshooting

#### Services won't start
```bash
# Check logs
docker-compose logs

# Rebuild images
docker-compose build --no-cache

# Remove all containers and volumes
docker-compose down -v
docker-compose up --build
```

#### Database connection error
```bash
# Wait for database to be ready
docker-compose exec backend python manage.py wait_for_db
```

#### Permission errors
```bash
# Fix ownership (Linux/Mac)
sudo chown -R $USER:$USER backend/
```

## Production Deployment

For production, create a separate `docker-compose.prod.yml`:

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    environment:
      - DEBUG=False
      - SECRET_KEY=${SECRET_KEY}
      # ... other prod settings
```

And a production Dockerfile:

```dockerfile
# backend/Dockerfile.prod
FROM python:3.11-slim

# Production optimizations
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies
COPY requirements/production.txt requirements/
RUN pip install -r requirements/production.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## Environment Variables

Create a `.env` file in the project root:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False

# Database
POSTGRES_DB=publicworks_db
POSTGRES_USER=publicworks
POSTGRES_PASSWORD=secure-password

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
```

Then update docker-compose.yml:

```yaml
services:
  backend:
    env_file:
      - .env
```

## Monitoring

### View Container Stats

```bash
docker stats
```

### Check Health

```bash
docker-compose ps
```

All services should show "Up (healthy)".

---

**Note**: For production, consider:
- Using managed PostgreSQL (AWS RDS, DigitalOcean, etc.)
- Using managed Redis (AWS ElastiCache, Redis Cloud, etc.)
- Adding Nginx reverse proxy
- SSL/TLS certificates
- Backup automation
- Monitoring (Sentry, DataDog, etc.)
