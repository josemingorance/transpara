"""Tests for base crawler functionality."""
from unittest.mock import Mock, patch

import pytest
from django.test import TestCase

from apps.contracts.models import RawContractData
from apps.crawlers.base import BaseCrawler, CrawlerException, HTMLCrawler, JSONCrawler
from apps.crawlers.models import CrawlerRun


class SimpleCrawler(BaseCrawler):
    """Test crawler implementation."""

    name = "test_crawler"
    source_platform = "TEST"
    source_url = "https://example.com"

    def __init__(self, **config):
        super().__init__(**config)
        self.fetch_called = False
        self.parse_called = False

    def fetch_raw(self):
        """Mock fetch."""
        self.fetch_called = True
        return "raw_data"

    def parse(self, raw):
        """Mock parse."""
        self.parse_called = True
        return [
            {
                "external_id": "TEST-001",
                "title": "Test Contract 1",
                "source_url": "https://example.com/1",
            },
            {
                "external_id": "TEST-002",
                "title": "Test Contract 2",
                "source_url": "https://example.com/2",
            },
        ]


class FailingCrawler(BaseCrawler):
    """Crawler that always fails."""

    name = "failing_crawler"
    source_platform = "FAIL"
    source_url = "https://example.com"

    def fetch_raw(self):
        """Raise exception."""
        raise CrawlerException("Fetch failed")

    def parse(self, raw):
        """Should not be called."""
        return []


@pytest.mark.django_db
class TestBaseCrawler(TestCase):
    """Test BaseCrawler functionality."""

    def test_crawler_initialization(self):
        """Test crawler initializes correctly."""
        crawler = SimpleCrawler(test_param="value")

        assert crawler.name == "test_crawler"
        assert crawler.source_platform == "TEST"
        assert crawler.config == {"test_param": "value"}
        assert crawler.session is not None

    def test_save_creates_records(self):
        """Test save creates RawContractData records."""
        crawler = SimpleCrawler()
        parsed_data = [
            {
                "external_id": "TEST-001",
                "title": "Test",
                "source_url": "https://example.com/1",
            }
        ]

        created, updated, failed = crawler.save(parsed_data)

        assert created == 1
        assert updated == 0
        assert failed == 0
        assert RawContractData.objects.count() == 1

        record = RawContractData.objects.first()
        assert record.external_id == "TEST-001"
        assert record.source_platform == "TEST"
        assert record.is_processed is False

    def test_save_updates_existing_records(self):
        """Test save updates existing records."""
        # Create existing record
        RawContractData.objects.create(
            source_platform="TEST",
            external_id="TEST-001",
            raw_data={"old": "data"},
        )

        crawler = SimpleCrawler()
        parsed_data = [
            {
                "external_id": "TEST-001",
                "title": "Updated",
                "source_url": "https://example.com/1",
            }
        ]

        created, updated, failed = crawler.save(parsed_data)

        assert created == 0
        assert updated == 1
        assert failed == 0
        assert RawContractData.objects.count() == 1

        record = RawContractData.objects.first()
        assert record.raw_data["title"] == "Updated"

    def test_save_handles_missing_external_id(self):
        """Test save handles items without external_id."""
        crawler = SimpleCrawler()
        parsed_data = [
            {"title": "No ID"},  # Missing external_id
        ]

        created, updated, failed = crawler.save(parsed_data)

        assert created == 0
        assert updated == 0
        assert failed == 1
        assert RawContractData.objects.count() == 0

    def test_run_crawler_success(self):
        """Test successful crawler execution."""
        crawler = SimpleCrawler()
        run = crawler.run_crawler()

        assert run.status == "SUCCESS"
        assert run.crawler_name == "test_crawler"
        assert run.records_found == 2
        assert run.records_created == 2
        assert run.records_updated == 0
        assert run.records_failed == 0
        assert run.duration_seconds is not None
        assert crawler.fetch_called
        assert crawler.parse_called

    def test_run_crawler_failure(self):
        """Test crawler handles failures gracefully."""
        crawler = FailingCrawler()
        run = crawler.run_crawler()

        assert run.status == "FAILED"
        assert run.crawler_name == "failing_crawler"
        assert "Fetch failed" in run.error_message
        assert run.duration_seconds is not None

    def test_run_crawler_creates_crawler_run(self):
        """Test run_crawler creates CrawlerRun record."""
        crawler = SimpleCrawler()
        run = crawler.run_crawler()

        assert CrawlerRun.objects.filter(id=run.id).exists()


@pytest.mark.django_db
class TestHTMLCrawler(TestCase):
    """Test HTMLCrawler functionality."""

    @patch("apps.crawlers.base.requests.Session.get")
    def test_fetch_raw_success(self, mock_get):
        """Test successful HTML fetch."""
        mock_response = Mock()
        mock_response.text = "<html>Test</html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        class TestHTMLCrawler(HTMLCrawler):
            name = "test_html"
            source_platform = "TEST"
            source_url = "https://example.com"

            def parse(self, raw):
                return []

        crawler = TestHTMLCrawler()
        result = crawler.fetch_raw()

        assert result == "<html>Test</html>"
        mock_get.assert_called_once()

    @patch("apps.crawlers.base.requests.Session.get")
    def test_fetch_raw_failure(self, mock_get):
        """Test HTML fetch failure handling."""
        mock_get.side_effect = Exception("Network error")

        class TestHTMLCrawler(HTMLCrawler):
            name = "test_html"
            source_platform = "TEST"
            source_url = "https://example.com"

            def parse(self, raw):
                return []

        crawler = TestHTMLCrawler()

        with pytest.raises(CrawlerException):
            crawler.fetch_raw()


@pytest.mark.django_db
class TestJSONCrawler(TestCase):
    """Test JSONCrawler functionality."""

    @patch("apps.crawlers.base.requests.Session.get")
    def test_fetch_raw_success(self, mock_get):
        """Test successful JSON fetch."""
        mock_response = Mock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        class TestJSONCrawler(JSONCrawler):
            name = "test_json"
            source_platform = "TEST"
            source_url = "https://api.example.com"

            def parse(self, raw):
                return []

        crawler = TestJSONCrawler()
        result = crawler.fetch_raw()

        assert result == {"data": "test"}

    @patch("apps.crawlers.base.requests.Session.get")
    def test_fetch_raw_invalid_json(self, mock_get):
        """Test invalid JSON handling."""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        class TestJSONCrawler(JSONCrawler):
            name = "test_json"
            source_platform = "TEST"
            source_url = "https://api.example.com"

            def parse(self, raw):
                return []

        crawler = TestJSONCrawler()

        with pytest.raises(CrawlerException):
            crawler.fetch_raw()
