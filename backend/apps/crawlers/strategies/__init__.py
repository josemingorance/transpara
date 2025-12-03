"""Strategy patterns for crawler implementations."""

from .discovery_strategies import (
    DiscoveryStrategy,
    SindicacionDiscoveryStrategy,
    GenericDiscoveryStrategy,
)
from .format_parsers import (
    FormatParser,
    CodiceFormatParser,
    LegacyFormatParser,
)

__all__ = [
    "DiscoveryStrategy",
    "SindicacionDiscoveryStrategy",
    "GenericDiscoveryStrategy",
    "FormatParser",
    "CodiceFormatParser",
    "LegacyFormatParser",
]
