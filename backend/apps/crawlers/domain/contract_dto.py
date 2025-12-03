"""Data Transfer Object for contract data.

Provides type-safe, validated data structure for contracts across the pipeline.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
from datetime import date


@dataclass
class ContractDTO:
    """Data Transfer Object for contract information.
    
    Provides a clean, type-safe interface for contract data throughout
    the crawler pipeline. All validation and type conversion should happen
    before creating this object.
    
    Attributes:
        external_id: Unique identifier from source platform
        title: Contract title/name
        description: Detailed description of the contract
        budget: Estimated budget value
        awarded_amount: Final awarded amount (if awarded)
        contracting_authority: Name of the contracting organization
        awarded_to_name: Name of awarded company/organization
        awarded_to_tax_id: Tax ID of awarded company
        publication_date: ISO date when contract was published
        deadline_date: ISO date for submission deadline
        award_date: ISO date when contract was awarded
        procedure_type: Type of procurement procedure
        contract_type: Type of contract (works, services, supplies)
        status: Current status of the contract
        source_url: URL to original contract listing
        region: Spanish autonomous community
        municipality: City or municipality name
    """
    
    # Required fields
    external_id: str
    title: str
    
    # Optional content fields
    description: str = ""
    
    # Financial fields
    budget: Optional[Decimal] = None
    awarded_amount: Optional[Decimal] = None
    
    # Organization fields
    contracting_authority: str = ""
    awarded_to_name: str = ""
    awarded_to_tax_id: Optional[str] = None
    
    # Date fields (ISO 8601 strings)
    publication_date: Optional[str] = None
    deadline_date: Optional[str] = None
    award_date: Optional[str] = None
    
    # Classification fields
    procedure_type: str = "OPEN"
    contract_type: str = "OTHER"
    status: str = "PUBLISHED"
    
    # Location fields
    region: str = ""
    municipality: str = ""
    
    # Source fields
    source_url: str = ""
    
    def to_dict(self) -> dict:
        """Convert DTO to dictionary for database storage.
        
        Returns:
            Dictionary representation of contract data
        """
        return {
            "external_id": self.external_id,
            "title": self.title,
            "description": self.description,
            "budget": float(self.budget) if self.budget else None,
            "awarded_amount": float(self.awarded_amount) if self.awarded_amount else None,
            "contracting_authority": self.contracting_authority,
            "awarded_to_name": self.awarded_to_name,
            "awarded_to_tax_id": self.awarded_to_tax_id,
            "publication_date": self.publication_date,
            "deadline_date": self.deadline_date,
            "award_date": self.award_date,
            "procedure_type": self.procedure_type,
            "contract_type": self.contract_type,
            "status": self.status,
            "region": self.region,
            "municipality": self.municipality,
            "source_url": self.source_url,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ContractDTO":
        """Create DTO from dictionary.
        
        Args:
            data: Dictionary with contract data
            
        Returns:
            ContractDTO instance
        """
        # Convert financial fields to Decimal if present
        budget = None
        if data.get("budget"):
            budget = Decimal(str(data["budget"]))
        
        awarded_amount = None
        if data.get("awarded_amount"):
            awarded_amount = Decimal(str(data["awarded_amount"]))
        
        return cls(
            external_id=data["external_id"],
            title=data["title"],
            description=data.get("description", ""),
            budget=budget,
            awarded_amount=awarded_amount,
            contracting_authority=data.get("contracting_authority", ""),
            awarded_to_name=data.get("awarded_to_name", ""),
            awarded_to_tax_id=data.get("awarded_to_tax_id"),
            publication_date=data.get("publication_date"),
            deadline_date=data.get("deadline_date"),
            award_date=data.get("award_date"),
            procedure_type=data.get("procedure_type", "OPEN"),
            contract_type=data.get("contract_type", "OTHER"),
            status=data.get("status", "PUBLISHED"),
            region=data.get("region", ""),
            municipality=data.get("municipality", ""),
            source_url=data.get("source_url", ""),
        )
    
    def is_valid(self) -> bool:
        """Check if contract has minimum required data.
        
        Returns:
            True if contract has valid external_id and title
        """
        return bool(self.external_id and self.title)
