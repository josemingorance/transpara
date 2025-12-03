"""Date parsing and conversion utilities.

Handles multiple date formats commonly found in Spanish public procurement data.
Provides consistent ISO 8601 output for database storage.
"""
from datetime import datetime
from typing import Optional
import logging


class DateHandler:
    """Handles date parsing and conversion to ISO format.
    
    Supports common Spanish and international date formats:
    - ISO 8601: YYYY-MM-DD
    - Spanish: DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
    - US: YYYY/MM/DD
    """
    
    SUPPORTED_FORMATS = [
        "%Y-%m-%d",      # 2025-11-29
        "%d/%m/%Y",      # 29/11/2025
        "%d-%m-%Y",      # 29-11-2025
        "%Y/%m/%d",      # 2025/11/29
        "%d.%m.%Y",      # 29.11.2025
        "%Y-%m-%dT%H:%M:%S",  # 2025-11-29T18:00:00
        "%Y-%m-%dT%H:%M:%S.%f",  # 2025-11-29T18:00:00.000
    ]
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize date handler.
        
        Args:
            logger: Optional logger for debugging
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def parse_to_iso(self, date_str: str) -> Optional[str]:
        """Parse date string to ISO 8601 format (YYYY-MM-DD).
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            ISO 8601 date string (YYYY-MM-DD) or None if parsing fails
            
        Examples:
            >>> handler = DateHandler()
            >>> handler.parse_to_iso("29/11/2025")
            '2025-11-29'
            >>> handler.parse_to_iso("2025-11-29")
            '2025-11-29'
        """
        if not date_str:
            return None
        
        # Clean input
        date_str = str(date_str).strip()
        
        # Try each supported format
        for fmt in self.SUPPORTED_FORMATS:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        self.logger.debug(f"Could not parse date: {date_str}")
        return None
    
    def is_valid_date(self, date_str: str) -> bool:
        """Check if string is a valid date.
        
        Args:
            date_str: Date string to validate
            
        Returns:
            True if valid date, False otherwise
        """
        return self.parse_to_iso(date_str) is not None
