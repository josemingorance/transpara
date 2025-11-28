"""
Base normalizer for ETL pipeline.

Provides foundation for transforming raw data into
normalized Contract models.
"""
import logging
from abc import ABC, abstractmethod
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.contracts.models import Contract, RawContractData
from apps.providers.models import Provider


class NormalizationException(Exception):
    """Exception raised during normalization."""

    pass


class BaseNormalizer(ABC):
    """
    Abstract base class for data normalizers.

    Each source platform should have its own normalizer
    that inherits from this base class.
    """

    source_platform: str = "unknown"

    def __init__(self) -> None:
        """Initialize normalizer."""
        self.logger = logging.getLogger(f"etl.{self.source_platform}")

    @abstractmethod
    def normalize(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize raw data to standard format.

        Args:
            raw_data: Raw data dictionary from crawler

        Returns:
            Normalized data dictionary matching Contract model

        Raises:
            NormalizationException: If normalization fails
        """
        pass

    def process_raw_record(self, raw_record: RawContractData) -> Contract | None:
        """
        Process a single RawContractData record.

        Args:
            raw_record: RawContractData instance

        Returns:
            Created or updated Contract instance, or None on failure
        """
        try:
            # Normalize the data
            normalized = self.normalize(raw_record.raw_data)

            # Create or update contract
            contract = self._save_contract(normalized, raw_record)

            # Mark raw record as processed
            raw_record.is_processed = True
            raw_record.processed_at = timezone.now()
            raw_record.contract = contract
            raw_record.save(update_fields=["is_processed", "processed_at", "contract"])

            self.logger.info(f"Processed: {contract.external_id}")
            return contract

        except Exception as e:
            # Log error and mark as failed
            self.logger.error(f"Failed to process {raw_record.external_id}: {e}")
            raw_record.processing_error = str(e)
            raw_record.save(update_fields=["processing_error"])
            return None

    @transaction.atomic
    def _save_contract(self, normalized: dict[str, Any], raw_record: RawContractData) -> Contract:
        """
        Save normalized data as Contract.

        Args:
            normalized: Normalized contract data
            raw_record: Source RawContractData

        Returns:
            Contract instance
        """
        external_id = normalized["external_id"]

        # Handle provider if specified
        awarded_to = None
        if "awarded_to_tax_id" in normalized and normalized["awarded_to_tax_id"]:
            awarded_to = self._get_or_create_provider(
                tax_id=normalized["awarded_to_tax_id"],
                name=normalized.get("awarded_to_name", "Unknown"),
            )

        # Create or update contract
        contract, created = Contract.objects.update_or_create(
            external_id=external_id,
            defaults={
                "title": normalized.get("title", ""),
                "description": normalized.get("description", ""),
                "contract_type": normalized.get("contract_type", "OTHER"),
                "status": normalized.get("status", "DRAFT"),
                "budget": normalized.get("budget", 0),
                "awarded_amount": normalized.get("awarded_amount"),
                "procedure_type": normalized.get("procedure_type", "OPEN"),
                "publication_date": normalized.get("publication_date"),
                "deadline_date": normalized.get("deadline_date"),
                "award_date": normalized.get("award_date"),
                "contracting_authority": normalized.get("contracting_authority", ""),
                "awarded_to": awarded_to,
                "region": normalized.get("region", ""),
                "province": normalized.get("province", ""),
                "municipality": normalized.get("municipality", ""),
                "source_url": normalized.get("source_url", ""),
                "source_platform": self.source_platform,
            },
        )

        action = "Created" if created else "Updated"
        self.logger.debug(f"{action}: {external_id}")

        return contract

    def _get_or_create_provider(self, tax_id: str, name: str) -> Provider:
        """
        Get or create a Provider.

        Args:
            tax_id: Provider tax ID
            name: Provider name

        Returns:
            Provider instance
        """
        provider, created = Provider.objects.get_or_create(
            tax_id=tax_id, defaults={"name": name}
        )
        return provider

    # Helper methods for common normalizations

    def parse_date(self, date_str: str | None) -> date | None:
        """
        Parse date string to date object.

        Args:
            date_str: Date string in various formats

        Returns:
            date object or None
        """
        if not date_str:
            return None

        try:
            # Try common formats
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            return None
        except Exception:
            return None

    def parse_money(self, money_str: str | float | None) -> Decimal:
        """
        Parse money string to Decimal.

        Args:
            money_str: Money string or number

        Returns:
            Decimal value
        """
        if not money_str:
            return Decimal("0")

        try:
            if isinstance(money_str, (int, float)):
                return Decimal(str(money_str))

            # Remove common currency symbols and spaces
            cleaned = str(money_str)
            for char in ["€", "$", "£", " ", "\xa0"]:
                cleaned = cleaned.replace(char, "")

            # Handle Spanish format (. for thousands, , for decimal)
            if "," in cleaned and "." in cleaned:
                # Determine which is decimal separator
                comma_pos = cleaned.rfind(",")
                dot_pos = cleaned.rfind(".")
                if comma_pos > dot_pos:
                    # Spanish format
                    cleaned = cleaned.replace(".", "").replace(",", ".")
                else:
                    # US format
                    cleaned = cleaned.replace(",", "")
            elif "," in cleaned:
                # Assume comma is decimal separator
                cleaned = cleaned.replace(",", ".")

            return Decimal(cleaned)

        except Exception:
            return Decimal("0")

    def normalize_contract_type(self, type_str: str | None) -> str:
        """
        Normalize contract type to standard choices.

        Args:
            type_str: Contract type string

        Returns:
            Standardized contract type
        """
        if not type_str:
            return "OTHER"

        type_lower = type_str.lower()

        if any(word in type_lower for word in ["obra", "work", "construcción", "construction"]):
            return "WORKS"
        elif any(
            word in type_lower for word in ["servicio", "service", "asistencia", "assistance"]
        ):
            return "SERVICES"
        elif any(
            word in type_lower
            for word in ["suministro", "suppl", "material", "equipo", "equipment"]
        ):
            return "SUPPLIES"
        elif "mixto" in type_lower or "mixed" in type_lower:
            return "MIXED"
        else:
            return "OTHER"

    def normalize_status(self, status_str: str | None) -> str:
        """
        Normalize contract status to standard choices.

        PLACSP status codes:
        - 'PUB' = Published
        - 'RES' = Resolved/Awarded
        - 'EJE' = Executing/In Progress
        - 'CAN' = Cancelled
        - 'FAL' = Failed
        - 'REV' = Revoked

        Args:
            status_str: Status string or code

        Returns:
            Standardized status
        """
        if not status_str:
            return "DRAFT"

        code = str(status_str).strip().upper()
        status_lower = code.lower()

        # Map PLACSP status codes
        placsp_map = {
            "PUB": "PUBLISHED",
            "RES": "AWARDED",
            "EJE": "IN_PROGRESS",
            "FAL": "CANCELLED",
            "CAN": "CANCELLED",
            "REV": "CANCELLED",
        }

        if code in placsp_map:
            return placsp_map[code]

        # Text matching for backwards compatibility
        if any(word in status_lower for word in ["published", "publicado", "active", "pub"]):
            return "PUBLISHED"
        elif any(word in status_lower for word in ["awarded", "adjudicado", "res"]):
            return "AWARDED"
        elif any(word in status_lower for word in ["completed", "finalizado", "cerrado"]):
            return "COMPLETED"
        elif any(word in status_lower for word in ["cancelled", "cancelado", "anulado", "can", "fal", "rev"]):
            return "CANCELLED"
        elif any(word in status_lower for word in ["progress", "ejecución", "eje"]):
            return "IN_PROGRESS"
        else:
            return "DRAFT"
