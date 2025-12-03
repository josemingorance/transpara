"""Format parsers for different ATOM entry structures.

Implements the Strategy pattern to handle different ATOM entry formats
found in PCSP data feeds (legacy embedded XML vs new CODICE format).
"""
from abc import ABC, abstractmethod
from typing import Optional, Protocol
import logging

from apps.crawlers.tools import PlacspFieldsExtractor, PlacspLicitacion


class FormatParser(Protocol):
    """Protocol for ATOM entry format parsers.
    
    Different ATOM entry formats require different extraction logic.
    """
    
    def can_parse(self, entry: any) -> bool:
        """Check if this parser can handle the entry format.
        
        Args:
            entry: AtomEntry object
            
        Returns:
            True if parser supports this format
        """
        ...
    
    def parse(self, entry: any) -> Optional[PlacspLicitacion]:
        """Parse ATOM entry to extract licitacion data.
        
        Args:
            entry: AtomEntry object
            
        Returns:
            PlacspLicitacion object or None if parsing fails
        """
        ...


class CodiceFormatParser:
    """Parser for new CODICE format ATOM entries.
    
    CODICE format has licitacion data as native ATOM elements,
    not embedded in content field.
    """
    
    def __init__(
        self,
        fields_extractor: PlacspFieldsExtractor,
        logger: logging.Logger
    ):
        """Initialize CODICE format parser.
        
        Args:
            fields_extractor: PlacspFieldsExtractor instance
            logger: Logger instance
        """
        self.fields_extractor = fields_extractor
        self.logger = logger
    
    def can_parse(self, entry: any) -> bool:
        """Check if entry is in CODICE format.
        
        Args:
            entry: AtomEntry object
            
        Returns:
            True if entry has raw_element with find() method
        """
        return (
            hasattr(entry, 'raw_element') and
            entry.raw_element is not None and
            hasattr(entry.raw_element, 'find')
        )
    
    def parse(self, entry: any) -> Optional[PlacspLicitacion]:
        """Parse CODICE format entry.
        
        Args:
            entry: AtomEntry object with raw_element
            
        Returns:
            PlacspLicitacion object or None
        """
        try:
            licitacion = self.fields_extractor.extract_from_atom_entry_element(
                entry.raw_element,
                entry.entry_id
            )
            
            if licitacion:
                # Add metadata from ATOM entry
                licitacion.identifier = entry.entry_id
                licitacion.update_date = entry.updated or ""
                
                self.logger.debug(f"Parsed CODICE format entry: {entry.entry_id}")
                return licitacion
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to parse CODICE entry {entry.entry_id}: {e}")
            return None


class LegacyFormatParser:
    """Parser for legacy format ATOM entries.
    
    Legacy format has licitacion data embedded as XML in content field.
    """
    
    def __init__(
        self,
        fields_extractor: PlacspFieldsExtractor,
        logger: logging.Logger
    ):
        """Initialize legacy format parser.
        
        Args:
            fields_extractor: PlacspFieldsExtractor instance
            logger: Logger instance
        """
        self.fields_extractor = fields_extractor
        self.logger = logger
    
    def can_parse(self, entry: any) -> bool:
        """Check if entry is in legacy format.
        
        Args:
            entry: AtomEntry object
            
        Returns:
            True if entry has content field with data
        """
        return hasattr(entry, 'content') and bool(entry.content)
    
    def parse(self, entry: any) -> Optional[PlacspLicitacion]:
        """Parse legacy format entry.
        
        Args:
            entry: AtomEntry object with content
            
        Returns:
            PlacspLicitacion object or None
        """
        try:
            licitacion = self.fields_extractor.extract_from_atom_entry_xml(
                entry.content,
                entry.entry_id
            )
            
            if licitacion:
                # Add metadata from ATOM entry
                licitacion.identifier = entry.entry_id
                licitacion.update_date = entry.updated or ""
                
                self.logger.debug(f"Parsed legacy format entry: {entry.entry_id}")
                return licitacion
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to parse legacy entry {entry.entry_id}: {e}")
            return None
