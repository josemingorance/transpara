"""ZIP discovery strategies for different PCSP data sources.

Implements the Strategy pattern to handle different approaches to discovering
available ZIP files from PCSP Datos Abiertos.
"""
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Protocol
import logging

import requests

from apps.crawlers.tools import PlacspZipInfo, ZipOrchestrator


class DiscoveryStrategy(Protocol):
    """Protocol for ZIP discovery strategies.
    
    Different sources may require different discovery approaches.
    """
    
    def discover(self, base_url: str) -> List[PlacspZipInfo]:
        """Discover available ZIP files from the given URL.
        
        Args:
            base_url: Base URL for data source
            
        Returns:
            List of PlacspZipInfo objects sorted chronologically
        """
        ...


class SindicacionDiscoveryStrategy:
    """Discovery strategy for sindicación URLs.
    
    Sindicación URLs don't have directory listings, so we probe for
    known filename patterns based on year-month combinations.
    
    Pattern: licitacionesPerfilesContratanteCompleto3_YYYYMM.zip
    """
    
    def __init__(
        self,
        session: requests.Session,
        logger: logging.Logger,
        months_to_check: int = 24
    ):
        """Initialize sindicación discovery strategy.
        
        Args:
            session: Requests session for HTTP calls
            logger: Logger instance
            months_to_check: Number of months backwards to check for ZIPs
        """
        self.session = session
        self.logger = logger
        self.months_to_check = months_to_check
    
    def discover(self, base_url: str, since_date: datetime | None = None) -> List[PlacspZipInfo]:
        """Discover ZIPs by probing known filename patterns.

        Optionally filters to only ZIPs from since_date onwards for incremental fetching.

        Args:
            base_url: Base sindicación URL
            since_date: Optional date to start fetching from (for incremental mode)

        Returns:
            List of available PlacspZipInfo objects sorted chronologically
        """
        zips = []
        today = datetime.now()

        # Determine minimum date to check
        min_date = since_date or (today - timedelta(days=30 * self.months_to_check))

        if since_date:
            self.logger.info(f"Incremental discovery: fetching ZIPs since {since_date.strftime('%Y-%m-%d')}")

        for months_back in range(self.months_to_check):
            date = today - timedelta(days=30 * months_back)

            # Skip dates before minimum (optimization to avoid unnecessary HEAD requests)
            if date < min_date:
                self.logger.debug(f"Skipping {date.strftime('%Y-%m')}: before since_date")
                break

            year_month = date.strftime("%Y%m")

            # Standard filename pattern for sindicación 643
            zip_filename = f"licitacionesPerfilesContratanteCompleto3_{year_month}.zip"
            zip_url = f"{base_url.rstrip('/')}/{zip_filename}"

            # Check if ZIP exists with HEAD request
            if self._zip_exists(zip_url):
                zip_info = PlacspZipInfo(
                    filename=zip_filename,
                    url=zip_url,
                    date=date,
                )
                zips.append(zip_info)
                self.logger.debug(f"Found ZIP: {zip_filename}")

        # Sort chronologically (oldest first)
        zips.sort()
        self.logger.info(f"Discovered {len(zips)} ZIPs via sindicación strategy")

        return zips
    
    def _zip_exists(self, url: str) -> bool:
        """Check if ZIP file exists at URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if ZIP exists (HTTP 200)
        """
        try:
            response = self.session.head(url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False


class GenericDiscoveryStrategy:
    """Discovery strategy for generic datosabiertos URLs.
    
    Uses ZipOrchestrator to parse directory listings and discover ZIPs.
    """
    
    def __init__(
        self,
        zip_orchestrator: ZipOrchestrator,
        logger: logging.Logger
    ):
        """Initialize generic discovery strategy.
        
        Args:
            zip_orchestrator: ZipOrchestrator instance for discovery
            logger: Logger instance
        """
        self.zip_orchestrator = zip_orchestrator
        self.logger = logger
    
    def discover(self, base_url: str, since_date: datetime | None = None) -> List[PlacspZipInfo]:
        """Discover ZIPs from directory listing.

        Optionally filters to only ZIPs from since_date onwards for incremental fetching.

        Args:
            base_url: Base URL with directory listing
            since_date: Optional date to start fetching from (for incremental mode)

        Returns:
            List of PlacspZipInfo objects in processing order
        """
        try:
            # Discover all available ZIPs
            zips = self.zip_orchestrator.discover_zips_from_url(base_url)

            if not zips:
                self.logger.info("No ZIPs found in directory listing")
                return []

            # Filter by date if since_date is provided (incremental mode)
            if since_date:
                original_count = len(zips)
                zips = [z for z in zips if z.date >= since_date]
                self.logger.info(
                    f"Incremental discovery: filtered {len(zips)}/{original_count} ZIPs "
                    f"since {since_date.strftime('%Y-%m-%d')}"
                )

            # Get chronological processing order
            ordered_zips = self.zip_orchestrator.get_processing_order(zips)

            self.logger.info(f"Discovered {len(ordered_zips)} ZIPs via generic strategy")
            return ordered_zips

        except Exception as e:
            self.logger.error(f"Failed to discover ZIPs: {e}")
            return []
