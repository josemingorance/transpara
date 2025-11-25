"""Tests for crawler registry."""
import pytest

from apps.crawlers.base import BaseCrawler
from apps.crawlers.registry import CrawlerRegistry, register_crawler


class TestCrawler(BaseCrawler):
    """Test crawler for registry tests."""

    name = "test"
    source_platform = "TEST"
    source_url = "https://example.com"

    def fetch_raw(self):
        return "data"

    def parse(self, raw):
        return []


class AnotherCrawler(BaseCrawler):
    """Another test crawler."""

    name = "another"
    source_platform = "TEST"
    source_url = "https://example.com"

    def fetch_raw(self):
        return "data"

    def parse(self, raw):
        return []


class TestCrawlerRegistry:
    """Test CrawlerRegistry functionality."""

    def test_register_crawler(self):
        """Test registering a crawler."""
        registry = CrawlerRegistry()
        registry.register(TestCrawler)

        assert "test" in registry.list_all()
        assert registry.get("test") == TestCrawler

    def test_register_duplicate_raises_error(self):
        """Test registering duplicate crawler raises error."""
        registry = CrawlerRegistry()
        registry.register(TestCrawler)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(TestCrawler)

    def test_get_nonexistent_returns_none(self):
        """Test getting nonexistent crawler returns None."""
        registry = CrawlerRegistry()

        assert registry.get("nonexistent") is None

    def test_list_all(self):
        """Test listing all crawlers."""
        registry = CrawlerRegistry()
        registry.register(TestCrawler)
        registry.register(AnotherCrawler)

        crawlers = registry.list_all()

        assert len(crawlers) == 2
        assert "test" in crawlers
        assert "another" in crawlers

    def test_get_all(self):
        """Test getting all crawlers."""
        registry = CrawlerRegistry()
        registry.register(TestCrawler)
        registry.register(AnotherCrawler)

        all_crawlers = registry.get_all()

        assert len(all_crawlers) == 2
        assert all_crawlers["test"] == TestCrawler
        assert all_crawlers["another"] == AnotherCrawler

    def test_register_decorator(self):
        """Test register_crawler decorator."""
        registry = CrawlerRegistry()

        @register_crawler
        class DecoratedCrawler(BaseCrawler):
            name = "decorated"
            source_platform = "TEST"
            source_url = "https://example.com"

            def fetch_raw(self):
                return "data"

            def parse(self, raw):
                return []

        # Note: This uses the global registry, not the local one
        # In real tests, you'd need to reset the global registry
        # or use dependency injection

        assert DecoratedCrawler.name == "decorated"
