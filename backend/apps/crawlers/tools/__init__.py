"""
Crawler tools and utilities.

This module contains shared tools and helpers used by different crawler implementations:
- atom_parser: ATOM/XML feed parsing with syndication support
- placsp_fields_extractor: PLACSP-specific field extraction
- zip_orchestrator: ZIP file discovery and processing orchestration
- concurrent_processor: Thread-based parallel processing infrastructure
"""

from .atom_parser import (
    AtomZipHandler,
    SyndicationChainFollower,
    AtomParseError,
    AtomFeed,
    AtomEntry,
)
from .placsp_fields_extractor import (
    PlacspFieldsExtractor,
    PlacspLicitacion,
)
from .zip_orchestrator import (
    ZipOrchestrator,
    PlacspZipInfo,
)
from .concurrent_processor import (
    ConcurrentProcessor,
    ZipConcurrentProcessor,
    FeedConcurrentProcessor,
    ProcessingStats,
)

__all__ = [
    "AtomZipHandler",
    "SyndicationChainFollower",
    "AtomParseError",
    "AtomFeed",
    "AtomEntry",
    "PlacspFieldsExtractor",
    "PlacspLicitacion",
    "ZipOrchestrator",
    "PlacspZipInfo",
    "ConcurrentProcessor",
    "ZipConcurrentProcessor",
    "FeedConcurrentProcessor",
    "ProcessingStats",
]
