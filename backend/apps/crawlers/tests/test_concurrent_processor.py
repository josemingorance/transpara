"""Tests for concurrent processor."""
import time
from unittest.mock import Mock, MagicMock
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.test import TestCase

from apps.crawlers.tools.concurrent_processor import (
    ConcurrentProcessor,
    ZipConcurrentProcessor,
    FeedConcurrentProcessor,
    RateLimiter,
    ProcessingStats,
    ProcessingResult,
)


class TestRateLimiter(TestCase):
    """Test rate limiter functionality."""
    
    def test_rate_limiter_initialization(self):
        """Test rate limiter initializes correctly."""
        limiter = RateLimiter(requests_per_second=5.0)
        assert limiter.requests_per_second == 5.0
        assert limiter.min_interval == 0.2
    
    def test_rate_limiter_enforces_delay(self):
        """Test rate limiter enforces minimum interval."""
        limiter = RateLimiter(requests_per_second=10.0)  # 100ms interval
        
        start = time.time()
        limiter.acquire()
        limiter.acquire()
        limiter.acquire()
        elapsed = time.time() - start
        
        # Should take at least 200ms for 3 requests (2 intervals)
        assert elapsed >= 0.19  # Allow small margin


class TestProcessingStats(TestCase):
    """Test processing statistics."""
    
    def test_empty_stats(self):
        """Test stats with no items."""
        stats = ProcessingStats()
        assert stats.success_rate == 0.0
        assert stats.average_duration == 0.0
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        stats = ProcessingStats(total_items=10, successful=8, failed=2)
        assert stats.success_rate == 80.0
    
    def test_average_duration(self):
        """Test average duration calculation."""
        stats = ProcessingStats(total_items=5, total_duration=10.0)
        assert stats.average_duration == 2.0


class TestConcurrentProcessor(TestCase):
    """Test concurrent processor base class."""
    
    def test_initialization(self):
        """Test processor initializes correctly."""
        processor = ConcurrentProcessor(
            max_workers=4,
            rate_limit=5.0,
            retry_attempts=3
        )
        assert processor.max_workers == 4
        assert processor.rate_limiter.requests_per_second == 5.0
    
    def test_session_with_retries(self):
        """Test session is created with retry configuration."""
        processor = ConcurrentProcessor(retry_attempts=3, retry_backoff=2.0)
        assert processor.session is not None
        assert processor.session.headers['User-Agent'].startswith('PublicWorksAI')
    
    def test_process_items_concurrent_success(self):
        """Test successful concurrent processing."""
        processor = ConcurrentProcessor(max_workers=2, rate_limit=100.0)
        
        # Mock processing function
        def mock_process(item):
            return {'id': item, 'processed': True}
        
        items = [1, 2, 3, 4, 5]
        results, stats = processor.process_items_concurrent(
            items=items,
            process_func=mock_process,
            item_name="test_item"
        )
        
        assert len(results) == 5
        assert stats.total_items == 5
        assert stats.successful == 5
        assert stats.failed == 0
        assert stats.success_rate == 100.0
    
    def test_process_items_with_failures(self):
        """Test processing with some failures."""
        processor = ConcurrentProcessor(max_workers=2, rate_limit=100.0)
        
        # Mock processing function that fails for even numbers
        def mock_process(item):
            if item % 2 == 0:
                raise ValueError(f"Failed on {item}")
            return {'id': item, 'processed': True}
        
        items = [1, 2, 3, 4, 5]
        results, stats = processor.process_items_concurrent(
            items=items,
            process_func=mock_process,
            item_name="test_item"
        )
        
        assert len(results) == 3  # Only odd numbers succeed
        assert stats.total_items == 5
        assert stats.successful == 3
        assert stats.failed == 2
        assert len(stats.errors) == 2
    
    def test_process_empty_list(self):
        """Test processing empty list."""
        processor = ConcurrentProcessor(max_workers=2)
        
        def mock_process(item):
            return item
        
        results, stats = processor.process_items_concurrent(
            items=[],
            process_func=mock_process,
            item_name="test"
        )
        
        assert len(results) == 0
        assert stats.total_items == 0
    
    def test_get_item_id(self):
        """Test item ID extraction."""
        processor = ConcurrentProcessor()
        
        # Test with object having filename
        item_with_filename = Mock(filename="test.zip")
        assert processor._get_item_id(item_with_filename) == "test.zip"
        
        # Test with dict
        item_dict = {'id': 'test-123', 'name': 'test'}
        assert processor._get_item_id(item_dict) == 'test-123'
        
        # Test with plain string
        item_str = "plain string item"
        assert processor._get_item_id(item_str) == "plain string item"
    
    def test_context_manager(self):
        """Test processor works as context manager."""
        with ConcurrentProcessor() as processor:
            assert processor is not None
            assert processor.session is not None


class TestZipConcurrentProcessor(TestCase):
    """Test ZIP concurrent processor."""
    
    def test_process_zips(self):
        """Test ZIP processing."""
        processor = ZipConcurrentProcessor(max_workers=2, rate_limit=100.0)
        
        # Mock ZIP info objects
        mock_zips = [
            Mock(filename=f"test_{i}.zip", url=f"http://test.com/{i}.zip")
            for i in range(3)
        ]
        
        # Mock processing function that returns contracts
        def mock_process_zip(zip_info):
            return [
                {'id': f'{zip_info.filename}_contract_1'},
                {'id': f'{zip_info.filename}_contract_2'},
            ]
        
        contracts, stats = processor.process_zips(
            zips=mock_zips,
            process_zip_func=mock_process_zip
        )
        
        assert len(contracts) == 6  # 3 ZIPs * 2 contracts each
        assert stats.total_items == 3
        assert stats.successful == 3


class TestFeedConcurrentProcessor(TestCase):
    """Test feed concurrent processor."""
    
    def test_process_entries(self):
        """Test entry processing."""
        processor = FeedConcurrentProcessor(max_workers=2, rate_limit=100.0)
        
        # Mock entries
        mock_entries = [
            Mock(entry_id=f"entry_{i}")
            for i in range(5)
        ]
        
        # Mock processing function
        def mock_process_entry(entry):
            return {'entry_id': entry.entry_id, 'processed': True}
        
        contracts, stats = processor.process_entries(
            entries=mock_entries,
            process_entry_func=mock_process_entry
        )
        
        assert len(contracts) == 5
        assert stats.total_items == 5
        assert stats.successful == 5


class TestConcurrencyBehavior(TestCase):
    """Test actual concurrent behavior."""
    
    def test_parallel_execution(self):
        """Test that tasks actually run in parallel."""
        processor = ConcurrentProcessor(max_workers=3, rate_limit=100.0)
        
        # Function that simulates work
        def slow_task(item):
            time.sleep(0.1)  # 100ms per task
            return {'result': item}  # Return a dict, not just the item
        
        items = list(range(6))
        
        start = time.time()
        results, stats = processor.process_items_concurrent(
            items=items,
            process_func=slow_task,
            item_name="slow_item"
        )
        elapsed = time.time() - start
        
        # With 3 workers and 6 items taking 100ms each:
        # Sequential would take 600ms, parallel should take ~200ms
        assert elapsed < 0.4  # Should be much faster than sequential
        assert stats.successful == 6
        assert stats.failed == 0
    
    def test_thread_safety(self):
        """Test that concurrent processing is thread-safe."""
        processor = ConcurrentProcessor(max_workers=4, rate_limit=100.0)
        
        shared_counter = {'count': 0}
        
        def increment_counter(item):
            # This is NOT thread-safe, testing processor handles it
            current = shared_counter['count']
            time.sleep(0.001)  # Simulate some work
            shared_counter['count'] = current + 1
            return {'item': item, 'processed': True}  # Return a dict
        
        items = list(range(20))
        results, stats = processor.process_items_concurrent(
            items=items,
            process_func=increment_counter,
            item_name="counter"
        )
        
        # All items should complete successfully
        assert stats.successful == 20
        assert stats.failed == 0


@pytest.mark.django_db
class TestIntegrationWithPCSP(TestCase):
    """Integration tests with PCSP crawler."""
    
    def test_concurrent_processor_import(self):
        """Test concurrent processor can be imported from tools."""
        from apps.crawlers.tools import (
            ZipConcurrentProcessor,
            FeedConcurrentProcessor,
            ProcessingStats
        )
        assert ZipConcurrentProcessor is not None
        assert FeedConcurrentProcessor is not None
        assert ProcessingStats is not None
    
    def test_pcsp_crawler_concurrent_config(self):
        """Test PCSP crawler accepts concurrent configuration."""
        from apps.crawlers.implementations.pcsp import PCSPCrawler
        
        crawler = PCSPCrawler(
            enable_concurrent=True,
            max_workers=4,
            rate_limit=10.0,
            retry_attempts=3
        )
        
        assert crawler.enable_concurrent is True
        assert crawler.max_workers == 4
        assert crawler.rate_limit == 10.0
        assert hasattr(crawler, 'zip_concurrent')
        assert hasattr(crawler, 'feed_concurrent')
