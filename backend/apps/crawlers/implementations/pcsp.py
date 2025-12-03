"""
PCSP (Plataforma de Contratación del Sector Público) crawler.

Collects contract data from Spain's national public procurement platform.
Uses official ATOMXML data feeds from Datos Abiertos PLACSP.

Refactored to follow SOLID principles with clean service-based architecture.
"""
from typing import Any, Optional
import logging

from apps.crawlers.base import CrawlerException, BaseCrawler
from apps.crawlers.registry import register_crawler

# Services
from apps.crawlers.services import (
    FetchService,
    ParsingService,
    DataDiscoveryService,
)

# Utilities
from apps.crawlers.utils import (
    DateHandler,
    MoneyHandler,
    RegionExtractor,
)

# Phase 1 tools
from apps.crawlers.tools import (
    AtomZipHandler,
    SyndicationChainFollower,
    PlacspFieldsExtractor,
    ZipOrchestrator,
)


@register_crawler
class PCSPCrawler(BaseCrawler):
    """Crawler for PCSP platform using clean SOLID architecture.
    
    This crawler fetches contract data from Spain's national public
    procurement platform (PCSP/PLACSP) using ATOM/XML feeds.
    
    Architecture follows SOLID principles:
    - Single Responsibility: Each service handles one aspect
    - Open/Closed: Extensible via strategy pattern
    - Dependency Inversion: Depends on abstractions (services)
    
    Data source: https://contrataciondelestado.es/wps/portal/plataforma/datos_abiertos/
    """
    
    name = "pcsp"
    source_platform = "PCSP"
    source_url = "https://contrataciondelestado.es/wps/portal/plataforma/datos_abiertos/"
    
    def __init__(self, **config):
        """Initialize PCSP crawler with dependency injection.
        
        Args:
            **config: Configuration options
        """
        super().__init__(**config)
        
        # Initialize utilities (reusable components)
        self.date_handler = DateHandler(logger=self.logger)
        self.money_handler = MoneyHandler(logger=self.logger)
        self.region_extractor = RegionExtractor(logger=self.logger)
        
        # Initialize Phase 1 tools
        self.zip_handler = AtomZipHandler(
            session=self.session,
            logger=self.logger
        )
        self.fields_extractor = PlacspFieldsExtractor(logger=self.logger)
        self.zip_orchestrator = ZipOrchestrator(
            session=self.session,
            logger=self.logger
        )
        self.chain_follower = SyndicationChainFollower(
            session=self.session,
            logger=self.logger
        )
        
        # Initialize services (with dependency injection)
        self.discovery_service = DataDiscoveryService(
            session=self.session,
            zip_orchestrator=self.zip_orchestrator,
            logger=self.logger
        )
        
        self.parsing_service = ParsingService(
            date_handler=self.date_handler,
            money_handler=self.money_handler,
            region_extractor=self.region_extractor,
            fields_extractor=self.fields_extractor,
            logger=self.logger
        )
        
        self.fetch_service = FetchService(
            discovery_service=self.discovery_service,
            parsing_service=self.parsing_service,
            zip_handler=self.zip_handler,
            zip_orchestrator=self.zip_orchestrator,
            chain_follower=self.chain_follower,
            logger=self.logger
        )
    
    def fetch_raw(self, incremental: bool = False, since_date: Any = None) -> list[dict]:
        """Fetch contract data from PCSP platform.

        Delegates to FetchService which handles:
        1. Discovery of available ZIP files
        2. Processing each ZIP's ATOM feeds
        3. Following syndication chains
        4. Extracting contract data

        Args:
            incremental: If True, only fetch data since last successful run
            since_date: Override date for incremental fetch (datetime or ISO string)

        Returns:
            List of raw contract dictionaries

        Raises:
            CrawlerException: If fatal error occurs
        """
        try:
            # Convert ISO string to datetime if needed
            since_datetime = None
            if since_date:
                if isinstance(since_date, str):
                    from datetime import datetime
                    since_datetime = datetime.fromisoformat(since_date)
                else:
                    since_datetime = since_date

            # Delegate to fetch service
            contracts = self.fetch_service.fetch_all(
                incremental=incremental,
                since_date=since_datetime
            )

            if not contracts:
                raise CrawlerException("No contracts fetched from PCSP")

            self.logger.info(
                f"Successfully fetched {len(contracts)} contracts from PCSP"
            )
            return contracts

        except Exception as e:
            raise CrawlerException(f"Failed to fetch PCSP data: {e}")
    
    def parse(self, raw: list[dict] | dict) -> list[dict]:
        """Parse PCSP response to extract contract details.
        
        Delegates to ParsingService which handles:
        1. Date parsing and normalization
        2. Money value conversion
        3. Region extraction
        4. Status and type inference
        
        Args:
            raw: List of contract dictionaries or wrapped response
            
        Returns:
            List of normalized contract dictionaries
            
        Raises:
            CrawlerException: If parsing fails
        """
        try:
            # Handle both list and dict responses
            if isinstance(raw, dict):
                contracts = raw.get("contracts", raw.get("items", raw.get("data", [])))
            elif isinstance(raw, list):
                contracts = raw
            else:
                return []
            
            # Delegate to parsing service
            parsed = self.parsing_service.parse_contracts(contracts)
            
            self.logger.info(f"Successfully parsed {len(parsed)} contracts")
            return parsed
            
        except Exception as e:
            raise CrawlerException(f"Failed to parse contracts: {e}")
