"""Fetch service for retrieving contract data from PCSP.

Orchestrates the data fetching process using Phase 1 tools.
Supports incremental mode to fetch only new data since last successful run.
Follows Single Responsibility Principle.
"""
from typing import List, Dict, Optional
from datetime import datetime
import logging

from apps.crawlers.tools import (
    AtomZipHandler,
    SyndicationChainFollower,
    PlacspZipInfo,
    ZipOrchestrator,
    AtomParseError,
    ZipConcurrentProcessor,
)
from apps.crawlers.services import DataDiscoveryService, ParsingService
from apps.crawlers.models import CrawlerRun


class FetchService:
    """Service for fetching contract data from PCSP platform.
    
    Coordinates the discovery, downloading, and processing of PCSP
    ZIP files containing ATOM feeds.
    
    Follows Single Responsibility Principle: Only responsible for
    orchestrating the fetch process, not for parsing or discovery details.
    """
    
    def __init__(
        self,
        discovery_service: DataDiscoveryService,
        parsing_service: ParsingService,
        zip_handler: AtomZipHandler,
        zip_orchestrator: ZipOrchestrator,
        chain_follower: SyndicationChainFollower,
        logger: logging.Logger
    ):
        """Initialize fetch service.
        
        Args:
            discovery_service: Service for discovering ZIPs
            parsing_service: Service for parsing entries
            zip_handler: Handler for ZIP operations
            zip_orchestrator: Orchestrator for ZIP processing
            chain_follower: Follower for syndication chains
            logger: Logger instance
        """
        self.discovery_service = discovery_service
        self.parsing_service = parsing_service
        self.zip_handler = zip_handler
        self.zip_orchestrator = zip_orchestrator
        self.chain_follower = chain_follower
        self.logger = logger
    
    def fetch_all(self, incremental: bool = False, since_date: Optional[datetime] = None) -> List[Dict]:
        """Fetch contract data from PCSP.

        Supports incremental mode to fetch only new data since last successful run.

        Args:
            incremental: If True, only fetch data since last successful run
            since_date: Override date for incremental fetch (if not provided, uses last run date)

        Returns:
            List of raw contract dictionaries
        """
        contracts = []

        try:
            # Determine since_date for incremental mode
            fetch_since_date = None
            if incremental:
                if since_date is None:
                    fetch_since_date = self._get_last_successful_run_date()

                    if fetch_since_date is None:
                        self.logger.warning(
                            "Incremental mode requested but no previous successful run found. "
                            "Falling back to full fetch (last 24 months)."
                        )
                    else:
                        self.logger.info(
                            f"Incremental mode: fetching data since {fetch_since_date.isoformat()}"
                        )
                else:
                    fetch_since_date = since_date
                    self.logger.info(
                        f"Incremental mode: fetching data since {fetch_since_date.isoformat()} "
                        f"(custom override)"
                    )

            # Try sindicación URL first (most recent data)
            base_url = "https://contrataciondelestado.es/sindicacion/sindicacion_643/"
            zips = self.discovery_service.discover_zips(base_url, since_date=fetch_since_date)

            # Fallback to generic datosabiertos if needed
            if not zips:
                self.logger.debug("No data in sindicación, trying generic datosabiertos")
                base_url = "https://contrataciondelestado.es/datosabiertos/"
                zips = self.discovery_service.discover_zips(base_url, since_date=fetch_since_date)

            if not zips:
                self.logger.info("No ZIPs found in PLACSP Datos Abiertos")
                return contracts

            self.logger.info(f"Processing {len(zips)} ZIP files with concurrent processing")

            # Use concurrent processor for parallel ZIP processing
            processor = ZipConcurrentProcessor(
                max_workers=6,  # 6 concurrent ZIP downloads
                rate_limit=3.0,  # 3 requests per second to avoid overwhelming server
                logger=self.logger
            )

            results, stats = processor.process_items_concurrent(
                items=zips,
                process_func=self._process_zip,
                item_name="ZIP"
            )

            # Flatten results from concurrent processing
            for result in results:
                if result:
                    contracts.extend(result)

            self.logger.info(
                f"Fetched {len(contracts)} total contracts "
                f"({stats.successful}/{stats.total_items} ZIPs processed, "
                f"{stats.success_rate:.1f}% success rate, "
                f"avg {stats.average_duration:.1f}s per ZIP)"
            )
            return contracts

        except Exception as e:
            self.logger.error(f"Error in fetch_all: {e}")
            return contracts

    def _get_last_successful_run_date(self) -> Optional[datetime]:
        """Get the completion date of the last successful crawler run.

        Returns:
            datetime of last successful run, or None if no successful run exists
        """
        try:
            last_run = CrawlerRun.objects.filter(
                crawler_name="pcsp",
                status="SUCCESS"
            ).order_by("-completed_at").first()

            if last_run and last_run.completed_at:
                return last_run.completed_at

            return None

        except Exception as e:
            self.logger.error(f"Failed to get last successful run date: {e}")
            return None
    
    def _process_zip(self, zip_info: PlacspZipInfo) -> List[Dict]:
        """Process a single ZIP file.
        
        Args:
            zip_info: Information about the ZIP to process
            
        Returns:
            List of contract dictionaries from this ZIP
        """
        contracts = []
        
        try:
            # Fetch and prepare ZIP
            zip_content, base_atom_filename = self.zip_orchestrator.fetch_and_prepare_zip(
                zip_info
            )
            
            if not base_atom_filename:
                self.logger.warning(f"Could not identify ATOM file in {zip_info.filename}")
                return contracts
            
            # Extract ATOM feed from ZIP
            feed = self.zip_handler.extract_atom_from_zip(zip_content, base_atom_filename)
            
            if not feed:
                return contracts
            
            self.logger.info(
                f"Processing ATOM from {zip_info.filename}: {len(feed.entries)} entries"
            )
            
            # Process feed entries
            contracts_from_feed = self._process_feed(feed)
            contracts.extend(contracts_from_feed)
            
            # Follow syndication chain if present
            if feed.next_url:
                self.logger.info(f"Following syndication chain: {feed.next_url}")
                contracts_from_chain = self._follow_chain(feed.next_url)
                contracts.extend(contracts_from_chain)
            
            return contracts
            
        except Exception as e:
            self.logger.error(f"Error processing ZIP {zip_info.filename}: {e}")
            return contracts
    
    def _process_feed(self, feed: any) -> List[Dict]:
        """Process all entries in an ATOM feed with concurrent processing.

        Args:
            feed: AtomFeed object

        Returns:
            List of contract dictionaries
        """
        from apps.crawlers.tools import FeedConcurrentProcessor

        if not feed.entries:
            return []

        # Use concurrent processor for parallel entry processing
        processor = FeedConcurrentProcessor(
            max_workers=4,  # 4 concurrent entry processors
            rate_limit=100.0,  # No rate limit for local processing
            logger=self.logger
        )

        results, stats = processor.process_items_concurrent(
            items=feed.entries,
            process_func=self._parse_entry_wrapper,
            item_name="entry"
        )

        self.logger.debug(
            f"Processed {len(feed.entries)} entries "
            f"({stats.successful} successful, {stats.failed} failed)"
        )

        return results

    def _parse_entry_wrapper(self, entry: any) -> Dict:
        """Wrapper for parsing a single entry (for concurrent processing).

        Args:
            entry: AtomEntry object

        Returns:
            Contract dictionary or None
        """
        try:
            licitacion = self.parsing_service.parse_atom_entry(entry)
            if licitacion:
                return licitacion.to_dict()
        except Exception as e:
            self.logger.warning(
                f"Failed to process entry {entry.entry_id}: {e}"
            )
        return None
    
    def _follow_chain(self, next_url: str) -> List[Dict]:
        """Follow syndication chain from URL.
        
        Args:
            next_url: URL to next feed in chain
            
        Returns:
            List of contract dictionaries from chain
        """
        contracts = []
        
        try:
            feeds = self.chain_follower.follow_chain(next_url, max_iterations=10)
            
            for feed in feeds:
                try:
                    contracts_from_feed = self._process_feed(feed)
                    contracts.extend(contracts_from_feed)
                except Exception as e:
                    self.logger.warning(f"Error processing feed in chain: {e}")
                    continue
                    
        except AtomParseError as e:
            self.logger.warning(f"Failed to follow chain from {next_url}: {e}")
        
        return contracts
