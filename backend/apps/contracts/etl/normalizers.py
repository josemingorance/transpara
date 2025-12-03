"""
Normalizers for specific data sources.

Each normalizer knows how to transform data from a specific
source platform into the standard Contract format.

Currently supported: PCSP (Plataforma de Contratación del Sector Público)
"""
from typing import Any

from apps.contracts.etl.base import BaseNormalizer


class PCSPNormalizer(BaseNormalizer):
    """
    Normalizer for PCSP (Plataforma de Contratación del Sector Público).

    Transforms PCSP-specific data structure to standard Contract format.
    """

    source_platform = "PCSP"

    def normalize(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize PCSP data.

        Transforms PCSP API response with complete financial and procurement details
        into standardized Contract format.

        Args:
            raw_data: Raw data from PCSP crawler

        Returns:
            Normalized contract data
        """
        # PCSP provides deadline_date not deadline
        deadline_key = "deadline_date" if "deadline_date" in raw_data else "deadline"

        return {
            "external_id": raw_data.get("external_id", ""),
            "title": raw_data.get("title", "").strip(),
            "description": raw_data.get("description", "").strip(),
            "contract_type": self.normalize_contract_type(raw_data.get("contract_type")),
            "status": self.normalize_status(raw_data.get("status")),
            "budget": self.parse_money(raw_data.get("budget")),
            "awarded_amount": self.parse_money(raw_data.get("awarded_amount")),
            "procedure_type": self._normalize_procedure_type(raw_data.get("procedure_type")),
            "publication_date": self.parse_date(raw_data.get("publication_date")),
            "deadline_date": self.parse_date(raw_data.get(deadline_key)),
            "award_date": self.parse_date(raw_data.get("award_date")),
            "contracting_authority": raw_data.get("contracting_authority", "").strip(),
            "awarded_to_tax_id": raw_data.get("awarded_to_tax_id"),
            "awarded_to_name": raw_data.get("awarded_to_name"),
            "region": raw_data.get("region", ""),
            "province": raw_data.get("province", ""),
            "municipality": raw_data.get("municipality", ""),
            "source_url": raw_data.get("source_url", ""),
        }

    def _normalize_procedure_type(self, proc_type: str | None) -> str:
        """
        Normalize procedure type for PCSP.

        PLACSP uses numeric codes:
        - '1' = Open procedure
        - '2' = Restricted procedure
        - '3' = Negotiated procedure
        - '4' = Competitive dialogue
        - '5' = Innovation partnership

        Args:
            proc_type: Procedure type string or code

        Returns:
            Standardized procedure type
        """
        if not proc_type:
            return "OPEN"

        code = str(proc_type).strip().lower()

        # Map numeric PLACSP codes
        placsp_map = {
            "1": "OPEN",
            "2": "RESTRICTED",
            "3": "NEGOTIATED",
            "4": "COMPETITIVE_DIALOGUE",
            "5": "COMPETITIVE_DIALOGUE",
        }

        if code in placsp_map:
            return placsp_map[code]

        # Text matching for backwards compatibility (matches Spanish keywords from PLACSP)
        if any(word in code for word in ["abierto", "open"]):
            return "OPEN"
        elif any(word in code for word in ["restringido", "restricted"]):
            return "RESTRICTED"
        elif any(word in code for word in ["negociado", "negotiated"]):
            return "NEGOTIATED"
        elif "menor" in code or "minor" in code:
            return "MINOR"
        elif any(
            word in code for word in ["diálogo", "dialogue", "competitivo", "competitive"]
        ):
            return "COMPETITIVE_DIALOGUE"
        else:
            return "OPEN"


# Registry of normalizers
NORMALIZERS = {
    "PCSP": PCSPNormalizer,
}


def get_normalizer(source_platform: str) -> BaseNormalizer | None:
    """
    Get normalizer for a source platform.

    Args:
        source_platform: Platform name

    Returns:
        Normalizer instance or None if not found
    """
    normalizer_class = NORMALIZERS.get(source_platform)
    if normalizer_class:
        return normalizer_class()
    return None
