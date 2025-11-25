"""
Base crawler classes.

Provides the foundation for all data collection crawlers
with consistent interface and error handling.
"""
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import requests
from django.db import transaction
from django.utils import timezone

from apps.contracts.models import RawContractData
from apps.crawlers.models import CrawlerRun


class CrawlerException(Exception):
    """Base exception for crawler errors."""

    pass


class BaseCrawler(ABC):
    """
    Abstract base crawler.

    All crawlers must inherit from this class and implement
    the required methods. Provides common functionality for
    error handling, logging, and data persistence.
    """

    # Override in subclasses
    name: str = "base_crawler"
    source_platform: str = "unknown"
    source_url: str = ""

    def __init__(self, **config: Any) -> None:
        """
        Initialize crawler.

        Args:
            **config: Additional configuration parameters
        """
        self.config = config
        self.logger = logging.getLogger(f"crawlers.{self.name}")
        self.session = requests.Session()
        self.run: CrawlerRun | None = None

        # Set default headers
        self.session.headers.update(
            {
                "User-Agent": "PublicWorksAI/1.0 (+https://publicworks.ai)",
            }
        )

    @abstractmethod
    def fetch_raw(self) -> Any:
        """
        Fetch raw data from source.

        Returns:
            Raw data in any format (HTML, JSON, etc.)

        Raises:
            CrawlerException: If fetching fails
        """
        pass

    @abstractmethod
    def parse(self, raw: Any) -> list[dict]:
        """
        Parse raw data into structured format.

        Args:
            raw: Raw data from fetch_raw()

        Returns:
            List of dictionaries with contract data

        Raises:
            CrawlerException: If parsing fails
        """
        pass

    def save(self, parsed_data: list[dict]) -> tuple[int, int, int]:
        """
        Save parsed data to database.

        Args:
            parsed_data: List of parsed contract dictionaries

        Returns:
            Tuple of (created, updated, failed) counts
        """
        created = 0
        updated = 0
        failed = 0

        for item in parsed_data:
            try:
                external_id = item.get("external_id")
                if not external_id:
                    self.logger.warning("Skipping item without external_id")
                    failed += 1
                    continue

                # Use get_or_create to handle duplicates
                raw_data, is_created = RawContractData.objects.get_or_create(
                    source_platform=self.source_platform,
                    external_id=external_id,
                    defaults={
                        "raw_data": item,
                        "source_url": item.get("source_url", ""),
                        "is_processed": False,
                    },
                )

                if is_created:
                    created += 1
                    self.logger.debug(f"Created: {external_id}")
                else:
                    # Update existing record
                    raw_data.raw_data = item
                    raw_data.source_url = item.get("source_url", "")
                    raw_data.save(update_fields=["raw_data", "source_url", "updated_at"])
                    updated += 1
                    self.logger.debug(f"Updated: {external_id}")

            except Exception as e:
                self.logger.error(f"Failed to save item: {e}")
                failed += 1

        return created, updated, failed

    def run_crawler(self) -> CrawlerRun:
        """
        Execute the complete crawler pipeline.

        Returns:
            CrawlerRun instance with execution details

        This is the main entry point - handles the entire
        fetch -> parse -> save flow with proper error handling
        and metrics tracking.
        """
        # Create run record
        self.run = CrawlerRun.objects.create(
            crawler_name=self.name,
            status="RUNNING",
            started_at=timezone.now(),
            config=self.config,
        )

        try:
            self.logger.info(f"Starting crawler: {self.name}")

            # Fetch raw data
            raw = self.fetch_raw()

            # Parse data
            parsed = self.parse(raw)
            self.run.records_found = len(parsed)
            self.run.save(update_fields=["records_found"])

            # Save to database
            created, updated, failed = self.save(parsed)

            # Update run with results
            self.run.status = "SUCCESS" if failed == 0 else "PARTIAL"
            self.run.records_created = created
            self.run.records_updated = updated
            self.run.records_failed = failed
            self.run.completed_at = timezone.now()

            # Calculate duration
            duration = (self.run.completed_at - self.run.started_at).total_seconds()
            self.run.duration_seconds = int(duration)

            self.logger.info(
                f"Completed: {created} created, {updated} updated, {failed} failed"
            )

        except Exception as e:
            self.logger.error(f"Crawler failed: {e}", exc_info=True)
            self.run.status = "FAILED"
            self.run.error_message = str(e)
            self.run.completed_at = timezone.now()

            # Calculate duration even on failure
            if self.run.started_at:
                duration = (self.run.completed_at - self.run.started_at).total_seconds()
                self.run.duration_seconds = int(duration)

        finally:
            self.run.save()
            self.session.close()

        return self.run


class HTMLCrawler(BaseCrawler):
    """Base class for HTML-based crawlers."""

    def fetch_raw(self) -> str:
        """
        Fetch HTML content.

        Returns:
            HTML string

        Raises:
            CrawlerException: If request fails
        """
        try:
            response = self.session.get(self.source_url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise CrawlerException(f"Failed to fetch HTML: {e}")


class JSONCrawler(BaseCrawler):
    """Base class for JSON API crawlers."""

    def fetch_raw(self) -> dict | list:
        """
        Fetch JSON data.

        Returns:
            Parsed JSON (dict or list)

        Raises:
            CrawlerException: If request fails
        """
        try:
            response = self.session.get(self.source_url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise CrawlerException(f"Failed to fetch JSON: {e}")
        except ValueError as e:
            raise CrawlerException(f"Invalid JSON response: {e}")
