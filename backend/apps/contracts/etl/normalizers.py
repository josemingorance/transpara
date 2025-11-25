"""
Normalizers for specific data sources.

Each normalizer knows how to transform data from a specific
source platform into the standard Contract format.
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

        Args:
            raw_data: Raw data from PCSP crawler

        Returns:
            Normalized contract data
        """
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
            "deadline_date": self.parse_date(raw_data.get("deadline")),
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

        Args:
            proc_type: Procedure type string

        Returns:
            Standardized procedure type
        """
        if not proc_type:
            return "OPEN"

        proc_lower = proc_type.lower()

        if any(word in proc_lower for word in ["abierto", "open"]):
            return "OPEN"
        elif any(word in proc_lower for word in ["restringido", "restricted"]):
            return "RESTRICTED"
        elif any(word in proc_lower for word in ["negociado", "negotiated"]):
            return "NEGOTIATED"
        elif "menor" in proc_lower or "minor" in proc_lower:
            return "MINOR"
        elif any(
            word in proc_lower for word in ["diálogo", "dialogue", "competitivo", "competitive"]
        ):
            return "COMPETITIVE_DIALOGUE"
        else:
            return "OPEN"


class BOENormalizer(BaseNormalizer):
    """
    Normalizer for BOE (Boletín Oficial del Estado).

    Handles data from official state gazette.
    """

    source_platform = "BOE"

    def normalize(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize BOE data.

        Args:
            raw_data: Raw data from BOE

        Returns:
            Normalized contract data
        """
        # BOE format is different - adjust as needed
        return {
            "external_id": raw_data.get("boe_id", raw_data.get("external_id", "")),
            "title": raw_data.get("titulo", raw_data.get("title", "")).strip(),
            "description": raw_data.get("texto", raw_data.get("description", "")).strip(),
            "contract_type": self.normalize_contract_type(
                raw_data.get("tipo_contrato", raw_data.get("contract_type"))
            ),
            "status": "PUBLISHED",  # BOE entries are always published
            "budget": self.parse_money(raw_data.get("presupuesto", raw_data.get("budget"))),
            "awarded_amount": self.parse_money(
                raw_data.get("importe_adjudicacion", raw_data.get("awarded_amount"))
            ),
            "procedure_type": self._normalize_procedure_type(
                raw_data.get("procedimiento", raw_data.get("procedure_type"))
            ),
            "publication_date": self.parse_date(
                raw_data.get("fecha_publicacion", raw_data.get("publication_date"))
            ),
            "deadline_date": self.parse_date(
                raw_data.get("plazo", raw_data.get("deadline_date"))
            ),
            "award_date": self.parse_date(
                raw_data.get("fecha_adjudicacion", raw_data.get("award_date"))
            ),
            "contracting_authority": raw_data.get(
                "organo_contratacion", raw_data.get("contracting_authority", "")
            ).strip(),
            "awarded_to_tax_id": raw_data.get("adjudicatario_cif"),
            "awarded_to_name": raw_data.get("adjudicatario_nombre"),
            "region": raw_data.get("comunidad", raw_data.get("region", "")),
            "province": raw_data.get("provincia", raw_data.get("province", "")),
            "municipality": raw_data.get("municipio", raw_data.get("municipality", "")),
            "source_url": raw_data.get("url", raw_data.get("source_url", "")),
        }

    def _normalize_procedure_type(self, proc_type: str | None) -> str:
        """Normalize BOE procedure type."""
        if not proc_type:
            return "OPEN"

        proc_lower = proc_type.lower()

        if any(word in proc_lower for word in ["abierto", "open"]):
            return "OPEN"
        elif any(word in proc_lower for word in ["restringido", "restricted"]):
            return "RESTRICTED"
        elif any(word in proc_lower for word in ["negociado", "negotiated"]):
            return "NEGOTIATED"
        elif "menor" in proc_lower:
            return "MINOR"
        else:
            return "OPEN"


# Registry of normalizers
NORMALIZERS = {
    "PCSP": PCSPNormalizer,
    "BOE": BOENormalizer,
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
