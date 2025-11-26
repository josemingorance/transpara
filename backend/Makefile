.PHONY: help install test lint format clean migrate run crawl normalize analyze pipeline

help:
	@echo "Available commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make install    - Install dependencies"
	@echo "  make migrate    - Run database migrations"
	@echo ""
	@echo "Development:"
	@echo "  make run        - Run development server"
	@echo "  make test       - Run tests with coverage"
	@echo "  make lint       - Run linters"
	@echo "  make format     - Format code with black and isort"
	@echo "  make clean      - Remove cache and temp files"
	@echo ""
	@echo "Data Pipeline (Simple):"
	@echo "  make crawl      - Run all crawlers (extract raw data)"
	@echo "  make normalize  - Normalize raw data to contracts"
	@echo "  make analyze    - Run risk analysis on contracts"
	@echo "  make pipeline   - Run complete pipeline (crawl → normalize → analyze)"
	@echo ""
	@echo "Data Pipeline (Advanced with reporting):"
	@echo "  make pipeline-full     - Run complete pipeline with report"
	@echo "  make pipeline-crawl    - Run crawlers only"
	@echo "  make pipeline-normalize - Run normalization only"
	@echo "  make pipeline-analyze   - Run analysis only"
	@echo "  make pipeline-report    - Generate execution report"

install:
	pip install -r requirements/local.txt

test:
	pytest

lint:
	flake8 .
	mypy .

format:
	black .
	isort .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov/

migrate:
	python manage.py makemigrations
	python manage.py migrate

run:
	python manage.py runserver

# Data Pipeline Commands

crawl:
	@echo "════════════════════════════════════════════"
	@echo "Step 1: Running crawlers..."
	@echo "════════════════════════════════════════════"
	python manage.py run_crawlers
	@echo ""

normalize:
	@echo "════════════════════════════════════════════"
	@echo "Step 2: Normalizing raw contract data..."
	@echo "════════════════════════════════════════════"
	python manage.py process_raw_data
	@echo ""

analyze:
	@echo "════════════════════════════════════════════"
	@echo "Step 3: Running risk analysis..."
	@echo "════════════════════════════════════════════"
	python manage.py analyze_risk --contracts
	@echo ""

pipeline: crawl normalize analyze
	@echo "════════════════════════════════════════════"
	@echo "✓ Complete pipeline executed successfully!"
	@echo "════════════════════════════════════════════"

# Advanced pipeline with report

pipeline-full:
	@bash .scripts/pipeline.sh pipeline

pipeline-crawl:
	@bash .scripts/pipeline.sh crawl

pipeline-normalize:
	@bash .scripts/pipeline.sh normalize

pipeline-analyze:
	@bash .scripts/pipeline.sh analyze

pipeline-report:
	@bash .scripts/pipeline.sh report
