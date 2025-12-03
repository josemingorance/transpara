"""Data discovery service for finding available data sources.

Implements service layer for ZIP discovery with pluggable strategies.
Supports incremental fetching to only discover new data since a given date.
Follows Single Responsibility Principle.
"""
from typing import List
from datetime import datetime
import logging

import requests

from apps.crawlers.tools import PlacspZipInfo, ZipOrchestrator
from apps.crawlers.strategies import (
    DiscoveryStrategy,
    SindicacionDiscoveryStrategy,
    GenericDiscoveryStrategy,
)


class DataDiscoveryService:
    """Service for discovering available PCSP data sources.
    
    Selects appropriate discovery strategy based on URL type and
    delegates the discovery work to that strategy.
    
    Follows Single Responsibility Principle: Only responsible for
    coordinating ZIP discovery, not for the actual discovery logic.
    """
    
    def __init__(
        self,
        session: requests.Session,
        zip_orchestrator: ZipOrchestrator,
        logger: logging.Logger
    ):
        """Initialize data discovery service.
        
        Args:
            session: Requests session for HTTP calls
            zip_orchestrator: ZipOrchestrator for generic discovery
            logger: Logger instance
        """
        self.session = session
        self.zip_orchestrator = zip_orchestrator
        self.logger = logger
    
    def discover_zips(self, base_url: str, since_date: datetime | None = None) -> List[PlacspZipInfo]:
        """Discover available ZIP files using appropriate strategy.

        Supports incremental mode to only discover ZIPs from a given date onwards.

        Args:
            base_url: Base URL for data source
            since_date: Optional date to filter ZIPs (for incremental fetching)

        Returns:
            List of PlacspZipInfo objects sorted chronologically
        """
        strategy = self._select_strategy(base_url)

        self.logger.info(
            f"Using {strategy.__class__.__name__} for URL: {base_url}"
        )

        return strategy.discover(base_url, since_date=since_date)
    
    def _select_strategy(self, base_url: str) -> DiscoveryStrategy:
        """Select appropriate discovery strategy based on URL.
        
        Args:
            base_url: URL to analyze
            
        Returns:
            Discovery strategy instance
        """
        # Sindicación URLs use pattern-based probing
        if "sindicacion" in base_url.lower():
            return SindicacionDiscoveryStrategy(
                session=self.session,
                logger=self.logger
            )
        
        # Generic URLs use directory listing
        return GenericDiscoveryStrategy(
            zip_orchestrator=self.zip_orchestrator,
            logger=self.logger
        )
