.PHONY: help install test lint format clean migrate run

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run tests with coverage"
	@echo "  make lint       - Run linters"
	@echo "  make format     - Format code with black and isort"
	@echo "  make clean      - Remove cache and temp files"
	@echo "  make migrate    - Run database migrations"
	@echo "  make run        - Run development server"

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
