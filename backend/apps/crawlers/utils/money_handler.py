"""Money value parsing and conversion utilities.

Handles money values in various formats including Spanish and US number formatting.
Provides Decimal output for financial precision.
"""
from decimal import Decimal, InvalidOperation
from typing import Any, Optional
import logging


class MoneyHandler:
    """Handles money value parsing and conversion to Decimal.
    
    Supports multiple number formats:
    - Spanish: 1.234.567,89 (dot as thousands separator, comma as decimal)
    - US/International: 1,234,567.89 (comma as thousands separator, dot as decimal)
    - Plain numbers: 1234567.89
    
    Also handles currency symbols (€, $, £) and whitespace.
    """
    
    CURRENCY_SYMBOLS = ["€", "$", "£", "USD", "EUR", "GBP", " ", "\xa0"]
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize money handler.
        
        Args:
            logger: Optional logger for debugging
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def parse_decimal(self, value: Any) -> Optional[Decimal]:
        """Parse money value to Decimal with proper precision.
        
        Args:
            value: Money value in various formats (string, float, int, Decimal)
            
        Returns:
            Decimal value or None if parsing fails
            
        Examples:
            >>> handler = MoneyHandler()
            >>> handler.parse_decimal("1.234,56")
            Decimal('1234.56')
            >>> handler.parse_decimal("1,234.56")
            Decimal('1234.56')
            >>> handler.parse_decimal("€ 1.000.000,00")
            Decimal('1000000.00')
        """
        if not value:
            return None
        
        try:
            # Handle numeric types directly
            if isinstance(value, Decimal):
                return value
            
            if isinstance(value, (int, float)):
                return Decimal(str(value))
            
            # Parse string
            cleaned = self._clean_money_string(str(value))
            
            if not cleaned:
                return None
            
            # Detect format and convert to standard decimal format
            cleaned = self._normalize_decimal_separators(cleaned)
            
            return Decimal(cleaned)
            
        except (InvalidOperation, ValueError) as e:
            self.logger.debug(f"Could not parse money value '{value}': {e}")
            return None
    
    def _clean_money_string(self, value: str) -> str:
        """Remove currency symbols and whitespace from money string.
        
        Args:
            value: Raw money string
            
        Returns:
            Cleaned string with only numbers and separators
        """
        cleaned = value
        
        # Remove currency symbols and whitespace
        for symbol in self.CURRENCY_SYMBOLS:
            cleaned = cleaned.replace(symbol, "")
        
        return cleaned.strip()
    
    def _normalize_decimal_separators(self, value: str) -> str:
        """Normalize decimal separators to standard format (dot as decimal).
        
        Handles both Spanish (1.234,56) and US (1,234.56) formats.
        
        Args:
            value: Cleaned money string with numbers and separators
            
        Returns:
            Normalized string with dot as decimal separator
        """
        # If both comma and dot present, determine which is decimal separator
        if "," in value and "." in value:
            comma_pos = value.rfind(",")
            dot_pos = value.rfind(".")
            
            if comma_pos > dot_pos:
                # Spanish format: 1.234,56 -> 1234.56
                value = value.replace(".", "").replace(",", ".")
            else:
                # US format: 1,234.56 -> 1234.56
                value = value.replace(",", "")
        
        # If only comma, assume it's decimal separator (Spanish format)
        elif "," in value:
            # Check if it's thousands separator or decimal
            # If more than 3 digits after comma, it's thousands separator
            parts = value.split(",")
            if len(parts) == 2 and len(parts[1]) <= 2:
                # Likely decimal: 1234,56
                value = value.replace(",", ".")
            # Otherwise keep as is (might be error)
        
        return value
    
    def format_money(self, value: Decimal, currency: str = "EUR") -> str:
        """Format Decimal as money string with currency.
        
        Args:
            value: Decimal value to format
            currency: Currency code (EUR, USD, GBP)
            
        Returns:
            Formatted money string
            
        Examples:
            >>> handler = MoneyHandler()
            >>> handler.format_money(Decimal("1234.56"), "EUR")
            '€1,234.56'
        """
        if value is None:
            return ""
        
        currency_symbols = {
            "EUR": "€",
            "USD": "$",
            "GBP": "£",
        }
        
        symbol = currency_symbols.get(currency, currency)
        formatted = f"{value:,.2f}"
        
        return f"{symbol}{formatted}"
