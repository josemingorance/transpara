"""
Concurrent processing infrastructure for PCSP crawler.

Provides thread-based parallel processing for ZIP files and ATOM feeds
to dramatically improve crawler performance while maintaining thread safety.
"""
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from queue import Queue
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass
class ProcessingResult:
    """Result from processing a single item."""
    
    item_id: str
    success: bool
    data: Any = None
    error: Optional[Exception] = None
    duration: float = 0.0


@dataclass
class ProcessingStats:
    """Statistics from concurrent processing."""
    
    total_items: int = 0
    successful: int = 0
    failed: int = 0
    total_duration: float = 0.0
    errors: list = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.successful / self.total_items) * 100
    
    @property
    def average_duration(self) -> float:
        """Calculate average processing time per item."""
        if self.total_items == 0:
            return 0.0
        return self.total_duration / self.total_items


class RateLimiter:
    """Thread-safe rate limiter using token bucket algorithm."""
    
    def __init__(self, requests_per_second: float = 5.0):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_second: Maximum requests per second
        """
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0
        self.lock = threading.Lock()
    
    def acquire(self):
        """Wait until a request can be made according to rate limit."""
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                wait_time = self.min_interval - time_since_last
                time.sleep(wait_time)
            
            self.last_request_time = time.time()


class ConcurrentProcessor:
    """
    Base concurrent processor with thread pool management.
    
    Provides infrastructure for parallel processing with:
    - Thread pool management
    - Connection pooling
    - Rate limiting
    - Error collection
    - Progress tracking
    """
    
    def __init__(
        self,
        max_workers: int = 8,
        rate_limit: float = 5.0,
        retry_attempts: int = 3,
        retry_backoff: float = 2.0,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize concurrent processor.
        
        Args:
            max_workers: Maximum number of concurrent threads
            rate_limit: Maximum requests per second
            retry_attempts: Number of retry attempts for failed requests
            retry_backoff: Backoff factor for retries
            logger: Optional logger instance
        """
        self.max_workers = max_workers
        self.logger = logger or logging.getLogger(__name__)
        self.rate_limiter = RateLimiter(requests_per_second=rate_limit)
        
        # Create session with connection pooling and retries
        self.session = self._create_session_with_retries(retry_attempts, retry_backoff)
        
        # Thread-safe error collection
        self.errors = Queue()
        self.error_lock = threading.Lock()
    
    def _create_session_with_retries(
        self, 
        retry_attempts: int, 
        retry_backoff: float
    ) -> requests.Session:
        """
        Create requests session with retry logic and connection pooling.
        
        Args:
            retry_attempts: Number of retry attempts
            retry_backoff: Backoff factor between retries
        
        Returns:
            Configured requests.Session
        """
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=retry_attempts,
            backoff_factor=retry_backoff,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        # Apply retry adapter with connection pooling
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=self.max_workers,
            pool_maxsize=self.max_workers * 2
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            "User-Agent": "PublicWorksAI/2.0 (+https://publicworks.ai)",
        })
        
        return session
    
    def process_items_concurrent(
        self,
        items: list,
        process_func: Callable,
        item_name: str = "item"
    ) -> tuple[list, ProcessingStats]:
        """
        Process items concurrently using thread pool.
        
        Args:
            items: List of items to process
            process_func: Function to process each item (must be thread-safe)
            item_name: Name for logging (e.g., "ZIP", "entry")
        
        Returns:
            Tuple of (results_list, processing_stats)
        """
        results = []
        stats = ProcessingStats(total_items=len(items))
        
        if not items:
            self.logger.info(f"No {item_name}s to process")
            return results, stats
        
        self.logger.info(f"Processing {len(items)} {item_name}s with {self.max_workers} workers")
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all items for processing
            future_to_item = {
                executor.submit(self._process_with_rate_limit, process_func, item, item_name): item
                for item in items
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    
                    if result.success:
                        stats.successful += 1
                        if result.data:
                            results.append(result.data)
                        self.logger.debug(f"✓ {item_name} {result.item_id} processed in {result.duration:.2f}s")
                    else:
                        stats.failed += 1
                        stats.errors.append({
                            'item_id': result.item_id,
                            'error': str(result.error)
                        })
                        self.logger.warning(f"✗ {item_name} {result.item_id} failed: {result.error}")
                    
                    stats.total_duration += result.duration
                    
                except Exception as e:
                    stats.failed += 1
                    stats.errors.append({
                        'item_id': str(item),
                        'error': str(e)
                    })
                    self.logger.error(f"✗ Unexpected error processing {item_name}: {e}")
        
        total_time = time.time() - start_time
        
        self.logger.info(
            f"Completed processing {len(items)} {item_name}s in {total_time:.2f}s: "
            f"{stats.successful} successful, {stats.failed} failed "
            f"({stats.success_rate:.1f}% success rate)"
        )
        
        return results, stats
    
    def _process_with_rate_limit(
        self,
        process_func: Callable,
        item: Any,
        item_name: str
    ) -> ProcessingResult:
        """
        Process single item with rate limiting.
        
        Args:
            process_func: Processing function
            item: Item to process
            item_name: Item type name for logging
        
        Returns:
            ProcessingResult
        """
        item_id = self._get_item_id(item)
        start_time = time.time()
        
        try:
            # Apply rate limiting
            self.rate_limiter.acquire()
            
            # Process item
            result_data = process_func(item)
            
            duration = time.time() - start_time
            return ProcessingResult(
                item_id=item_id,
                success=True,
                data=result_data,
                duration=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.debug(f"Error processing {item_name} {item_id}: {e}")
            return ProcessingResult(
                item_id=item_id,
                success=False,
                error=e,
                duration=duration
            )
    
    def _get_item_id(self, item: Any) -> str:
        """Extract identifier from item for logging."""
        if hasattr(item, 'filename'):
            return item.filename
        elif hasattr(item, 'entry_id'):
            return item.entry_id
        elif hasattr(item, 'id'):
            return str(item.id)
        elif isinstance(item, dict):
            return item.get('id', item.get('filename', str(item)[:50]))
        else:
            return str(item)[:50]
    
    def cleanup(self):
        """Clean up resources."""
        if hasattr(self, 'session'):
            self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()


class ZipConcurrentProcessor(ConcurrentProcessor):
    """Specialized concurrent processor for ZIP files."""
    
    def process_zips(
        self,
        zips: list,
        process_zip_func: Callable
    ) -> tuple[list, ProcessingStats]:
        """
        Process multiple ZIP files concurrently.
        
        Args:
            zips: List of PlacspZipInfo objects
            process_zip_func: Function to process a single ZIP
        
        Returns:
            Tuple of (all_contracts, stats)
        """
        all_contracts = []
        
        # Process ZIPs concurrently
        zip_results, stats = self.process_items_concurrent(
            items=zips,
            process_func=process_zip_func,
            item_name="ZIP"
        )
        
        # Flatten results (each ZIP returns a list of contracts)
        for contracts in zip_results:
            if contracts:
                all_contracts.extend(contracts)
        
        self.logger.info(f"Extracted {len(all_contracts)} total contracts from {stats.successful} ZIPs")
        
        return all_contracts, stats


class FeedConcurrentProcessor(ConcurrentProcessor):
    """Specialized concurrent processor for ATOM feed entries."""
    
    def process_entries(
        self,
        entries: list,
        process_entry_func: Callable
    ) -> tuple[list, ProcessingStats]:
        """
        Process ATOM feed entries concurrently.
        
        Args:
            entries: List of AtomEntry objects
            process_entry_func: Function to process a single entry
        
        Returns:
            Tuple of (contracts, stats)
        """
        contracts, stats = self.process_items_concurrent(
            items=entries,
            process_func=process_entry_func,
            item_name="entry"
        )
        
        return contracts, stats
