"""
Crawler registry.

Central registry for managing and discovering crawlers.
"""
from typing import Type

from apps.crawlers.base import BaseCrawler


class CrawlerRegistry:
    """
    Registry for all available crawlers.

    Provides a central place to register and retrieve
    crawler classes by name.
    """

    def __init__(self) -> None:
        self._crawlers: dict[str, Type[BaseCrawler]] = {}

    def register(self, crawler_class: Type[BaseCrawler]) -> None:
        """
        Register a crawler class.

        Args:
            crawler_class: Crawler class to register

        Raises:
            ValueError: If crawler name is already registered
        """
        name = crawler_class.name
        if name in self._crawlers:
            raise ValueError(f"Crawler '{name}' is already registered")
        self._crawlers[name] = crawler_class

    def get(self, name: str) -> Type[BaseCrawler] | None:
        """
        Get crawler class by name.

        Args:
            name: Crawler name

        Returns:
            Crawler class or None if not found
        """
        return self._crawlers.get(name)

    def list_all(self) -> list[str]:
        """
        List all registered crawler names.

        Returns:
            List of crawler names
        """
        return list(self._crawlers.keys())

    def get_all(self) -> dict[str, Type[BaseCrawler]]:
        """
        Get all registered crawlers.

        Returns:
            Dictionary mapping names to crawler classes
        """
        return self._crawlers.copy()


# Global registry instance
registry = CrawlerRegistry()


def register_crawler(crawler_class: Type[BaseCrawler]) -> Type[BaseCrawler]:
    """
    Decorator to register a crawler.

    Usage:
        @register_crawler
        class MyCrawler(BaseCrawler):
            ...

    Args:
        crawler_class: Crawler class to register

    Returns:
        The same crawler class (for chaining)
    """
    registry.register(crawler_class)
    return crawler_class
