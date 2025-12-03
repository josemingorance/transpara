"""Parsing service for contract data transformation.

Orchestrates parsing of raw contract data using utilities and strategies.
Follows Single Responsibility Principle.
"""
from decimal import Decimal
from typing import List, Dict, Optional
import logging

from apps.crawlers.domain import ContractDTO
from apps.crawlers.utils import DateHandler, MoneyHandler, RegionExtractor
from apps.crawlers.strategies import FormatParser, CodiceFormatParser, LegacyFormatParser
from apps.crawlers.tools import PlacspFieldsExtractor, PlacspLicitacion


class ParsingService:
    """Service for parsing and transforming contract data.
    
    Coordinates the parsing of raw contract data into ContractDTO objects.
    Uses injected utilities and strategies for specific transformations.
    
    Follows Single Responsibility Principle: Only responsible for
    orchestrating parsing, not for specific parsing logic.
    """
    
    def __init__(
        self,
        date_handler: DateHandler,
        money_handler: MoneyHandler,
        region_extractor: RegionExtractor,
        fields_extractor: PlacspFieldsExtractor,
        logger: logging.Logger
    ):
        """Initialize parsing service.
        
        Args:
            date_handler: Handler for date parsing
            money_handler: Handler for money parsing
            region_extractor: Extractor for region information
            fields_extractor: PLACSP fields extractor
            logger: Logger instance
        """
        self.date_handler = date_handler
        self.money_handler = money_handler
        self.region_extractor = region_extractor
        self.fields_extractor = fields_extractor
        self.logger = logger
        
        # Initialize format parsers
        self.format_parsers: List[FormatParser] = [
            CodiceFormatParser(fields_extractor, logger),
            LegacyFormatParser(fields_extractor, logger),
        ]
    
    def parse_contracts(self, raw_contracts: List[Dict]) -> List[Dict]:
        """Parse list of raw contract dictionaries.
        
        Args:
            raw_contracts: List of raw contract data from PCSP
            
        Returns:
            List of normalized contract dictionaries
        """
        parsed = []
        
        for raw_contract in raw_contracts:
            try:
                contract_dto = self.parse_single_contract(raw_contract)
                
                if contract_dto and contract_dto.is_valid():
                    parsed.append(contract_dto.to_dict())
                else:
                    self.logger.debug(
                        f"Skipping invalid contract: {raw_contract.get('id')}"
                    )
                    
            except Exception as e:
                self.logger.warning(
                    f"Failed to parse contract {raw_contract.get('id', 'unknown')}: {e}"
                )
                continue
        
        self.logger.info(f"Successfully parsed {len(parsed)}/{len(raw_contracts)} contracts")
        return parsed
    
    def parse_single_contract(self, raw_data: Dict) -> Optional[ContractDTO]:
        """Parse single contract from raw data.
        
        Args:
            raw_data: Raw contract dictionary
            
        Returns:
            ContractDTO or None if parsing fails
        """
        # Extract required fields
        external_id = self._extract_external_id(raw_data)
        title = self._extract_title(raw_data)
        
        if not external_id or not title:
            return None
        
        # Parse financial fields
        budget = self._parse_budget(raw_data)
        awarded_amount = self._parse_awarded_amount(raw_data)
        
        # Parse dates
        publication_date = self._parse_publication_date(raw_data)
        deadline_date = self._parse_deadline_date(raw_data)
        award_date = self._parse_award_date(raw_data)
        
        # Extract organization fields
        authority = raw_data.get("contracting_authority", "").strip()
        awarded_to_name, awarded_to_tax_id = self._extract_awarded_to(raw_data)
        
        # Parse classification fields
        procedure_type = self._map_procedure_type(
            raw_data.get("procedure_type") or raw_data.get("procedureType", "")
        )
        contract_type = self._infer_contract_type(
            raw_data.get("contract_type") or raw_data.get("contractType", ""),
            title
        )
        status = self._infer_status(raw_data)
        
        # Extract location
        region = raw_data.get("region", "") or self.region_extractor.extract_region(authority)
        municipality = raw_data.get("municipality") or raw_data.get("execution_place_name", "")
        
        # Create DTO
        return ContractDTO(
            external_id=external_id,
            title=title.strip(),
            description=raw_data.get("description") or raw_data.get("contract_object", ""),
            budget=budget,
            awarded_amount=awarded_amount,
            contracting_authority=authority,
            awarded_to_name=awarded_to_name,
            awarded_to_tax_id=awarded_to_tax_id,
            publication_date=publication_date,
            deadline_date=deadline_date,
            award_date=award_date,
            procedure_type=procedure_type,
            contract_type=contract_type,
            status=status,
            region=region,
            municipality=municipality,
            source_url=raw_data.get("url") or raw_data.get("link", ""),
        )
    
    def parse_atom_entry(self, entry: any) -> Optional[PlacspLicitacion]:
        """Parse ATOM entry using appropriate format parser.
        
        Args:
            entry: AtomEntry object
            
        Returns:
            PlacspLicitacion or None
        """
        for parser in self.format_parsers:
            if parser.can_parse(entry):
                return parser.parse(entry)
        
        self.logger.warning(f"No parser found for entry: {entry.entry_id}")
        return None
    
    # Helper methods for extraction and transformation
    
    def _extract_external_id(self, data: Dict) -> Optional[str]:
        """Extract external ID from various field names."""
        return (
            data.get("id") or
            data.get("identifier") or
            data.get("contractNumber")
        )
    
    def _extract_title(self, data: Dict) -> Optional[str]:
        """Extract title from various field names."""
        return (
            data.get("title") or
            data.get("contract_object") or
            data.get("name", "")
        )
    
    def _parse_budget(self, data: Dict) -> Optional[Decimal]:
        """Parse budget value."""
        value = (
            data.get("budget_without_taxes") or
            data.get("budget") or
            data.get("estimatedValue") or
            data.get("amount")
        )
        return self.money_handler.parse_decimal(value)
    
    def _parse_awarded_amount(self, data: Dict) -> Optional[Decimal]:
        """Parse awarded amount value."""
        value = data.get("awardedAmount") or data.get("finalAmount")
        return self.money_handler.parse_decimal(value)
    
    def _parse_publication_date(self, data: Dict) -> Optional[str]:
        """Parse publication date."""
        date_str = (
            data.get("first_publication_date") or
            data.get("publicationDate") or
            data.get("createdAt")
        )
        return self.date_handler.parse_to_iso(date_str)
    
    def _parse_deadline_date(self, data: Dict) -> Optional[str]:
        """Parse deadline date."""
        date_str = data.get("deadline") or data.get("closingDate")
        return self.date_handler.parse_to_iso(date_str)
    
    def _parse_award_date(self, data: Dict) -> Optional[str]:
        """Parse award date from various sources."""
        date_str = (
            data.get("award_date") or
            data.get("awardDate") or
            data.get("finalizedDate")
        )
        
        # Try direct fields first
        if date_str:
            return self.date_handler.parse_to_iso(date_str)
        
        # Check results array for award date
        if data.get("results"):
            for result in data["results"]:
                if result.get("award_date"):
                    return self.date_handler.parse_to_iso(result["award_date"])
        
        return None
    
    def _extract_awarded_to(self, data: Dict) -> tuple[str, Optional[str]]:
        """Extract awarded company name and tax ID."""
        awarded_to = data.get("awardedTo") or data.get("winner", {})
        
        if isinstance(awarded_to, dict):
            name = awarded_to.get("name", "").strip()
            tax_id = awarded_to.get("taxId") or awarded_to.get("cif")
        else:
            name = str(awarded_to).strip() if awarded_to else ""
            tax_id = None
        
        return name, tax_id
    
    def _map_procedure_type(self, procedure_type_raw: str) -> str:
        """Map PLACSP procedure type codes to standard types."""
        if not procedure_type_raw:
            return "OPEN"
        
        code = str(procedure_type_raw).strip().lower()
        
        # PLACSP numeric codes
        code_map = {
            "1": "OPEN",
            "2": "RESTRICTED",
            "3": "NEGOTIATED",
            "4": "COMPETITIVE_DIALOGUE",
            "5": "COMPETITIVE_DIALOGUE",
        }
        
        if code in code_map:
            return code_map[code]
        
        # Text matching (Spanish keywords match PLACSP external data)
        if any(word in code for word in ["abierto", "open"]):
            return "OPEN"
        elif any(word in code for word in ["restringido", "restricted"]):
            return "RESTRICTED"
        elif any(word in code for word in ["negociado", "negotiated"]):
            return "NEGOTIATED"
        elif any(word in code for word in ["diálogo", "dialogue"]):
            return "COMPETITIVE_DIALOGUE"
        
        return "OPEN"
    
    def _infer_status(self, data: Dict) -> str:
        """Infer contract status from data."""
        status = str(data.get("status", "")).strip().upper()
        
        # PLACSP status codes mapping
        status_map = {
            "RES": "AWARDED",
            "PUB": "PUBLISHED",
            "EJE": "IN_PROGRESS",
            "FAL": "CANCELLED",
            "CAN": "CANCELLED",
            "REV": "CANCELLED",
        }
        
        if status in status_map:
            return status_map[status]
        
        # Text matching (Spanish keywords match PLACSP external data)
        status_lower = status.lower()
        if any(word in status_lower for word in ["awarded", "adjudicado", "res"]):
            return "AWARDED"
        elif any(word in status_lower for word in ["completed", "finalizado", "cerrado"]):
            return "COMPLETED"
        elif any(word in status_lower for word in ["cancelled", "cancelado", "anulado"]):
            return "CANCELLED"
        elif any(word in status_lower for word in ["progress", "ejecución", "eje"]):
            return "IN_PROGRESS"
        
        return "PUBLISHED"
    
    def _infer_contract_type(self, contract_type: str, title: str) -> str:
        """Infer standardized contract type.

        Note: Spanish keywords (obra, servicio, suministro) match PLACSP external data.
        Handles both singular and plural forms.
        """
        type_lower = (contract_type or "").lower()
        title_lower = (title or "").lower()
        combined = f"{type_lower} {title_lower}"

        if any(word in combined
               for word in ["obra", "construcción", "infraestructura", "work"]):
            return "WORKS"
        elif any(word in combined
                 for word in ["servicio", "asistencia", "consultoría", "service"]):
            return "SERVICES"
        elif any(word in combined
                 for word in ["suministro", "material", "equipo", "supply", "supplies"]):
            return "SUPPLIES"
        elif "mixto" in combined or "mixed" in combined:
            return "MIXED"

        return "OTHER"
