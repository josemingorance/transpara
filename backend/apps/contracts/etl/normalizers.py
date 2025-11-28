"""
Normalizers for specific data sources.

Each normalizer knows how to transform data from a specific
source platform into the standard Contract format.
"""
from decimal import Decimal
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
        - '1' = Open procedure (Procedimiento abierto)
        - '2' = Restricted procedure (Procedimiento restringido)
        - '3' = Negotiated procedure (Procedimiento negociado)
        - '4' = Competitive dialogue (Diálogo competitivo)
        - '5' = Innovation partnership (Asociación para innovación)

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

        # Text matching for backwards compatibility
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


class BOENormalizer(BaseNormalizer):
    """
    Normalizer for BOE (Boletín Oficial del Estado).

    Transforms data extracted from the BOE API JSON responses
    into the standard Contract format.
    """

    source_platform = "BOE"

    def normalize(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """
        Normalize BOE API data.

        Transforms BOE crawler output (from JSON API) to standard Contract fields.

        Args:
            raw_data: Raw data from BOE crawler

        Returns:
            Normalized contract data dictionary
        """
        # Extract the item_type and determine contract type
        item_type = raw_data.get("item_type", "OTHER")
        contract_type = self._infer_contract_type(item_type, raw_data)

        return {
            "external_id": raw_data.get("external_id", ""),
            "title": raw_data.get("title", "").strip(),
            "description": self._build_description(raw_data),
            "contract_type": contract_type,
            "status": "PUBLISHED",  # All BOE items are published by definition
            "budget": Decimal("0"),  # BOE API responses don't include budget info
            "awarded_amount": None,  # BOE API responses don't include awarded amounts
            "procedure_type": self._infer_procedure_type(item_type),
            "publication_date": self.parse_date(raw_data.get("publication_date")),
            "deadline_date": None,  # BOE API doesn't provide deadline
            "award_date": None,  # BOE API doesn't provide award date
            "contracting_authority": raw_data.get("contracting_authority", "").strip(),
            "awarded_to_tax_id": None,  # BOE API doesn't provide awarded provider info
            "awarded_to_name": None,
            "region": self._extract_region_from_boe(raw_data),
            "province": "",
            "municipality": "",
            "source_url": raw_data.get("source_url", ""),
        }

    def _build_description(self, raw_data: dict[str, Any]) -> str:
        """
        Build a description from BOE item metadata.

        Args:
            raw_data: Raw BOE data

        Returns:
            Combined description string
        """
        parts = []

        section = raw_data.get("section", "").strip()
        if section:
            parts.append(f"Section: {section}")

        subsection = raw_data.get("subsection", "").strip()
        if subsection:
            parts.append(f"Subsection: {subsection}")

        item_type = raw_data.get("item_type", "").strip()
        if item_type:
            parts.append(f"Type: {item_type}")

        return " | ".join(parts) if parts else ""

    def _infer_contract_type(self, item_type: str, raw_data: dict[str, Any]) -> str:
        """
        Infer contract type from BOE item type and title.

        Args:
            item_type: BOE item type classification
            raw_data: Raw BOE data

        Returns:
            Standardized contract type
        """
        if item_type == "CONTRACT":
            return "SUPPLIES"  # BOE contracts are typically supplies

        # Check title and section for type hints
        title_lower = raw_data.get("title", "").lower()
        section_lower = raw_data.get("section", "").lower()

        if any(word in title_lower or word in section_lower for word in ["obra", "construcción", "work"]):
            return "WORKS"
        elif any(
            word in title_lower or word in section_lower
            for word in ["servicio", "asistencia", "service", "assistance"]
        ):
            return "SERVICES"
        elif any(
            word in title_lower or word in section_lower
            for word in ["suministro", "equipo", "material", "supplies", "equipment"]
        ):
            return "SUPPLIES"
        else:
            return "OTHER"

    def _infer_procedure_type(self, item_type: str) -> str:
        """
        Infer procedure type from BOE item type.

        Args:
            item_type: BOE item type classification

        Returns:
            Standardized procedure type
        """
        if item_type == "ANNOUNCEMENT":
            return "OPEN"  # Announcements are typically open procedures
        elif item_type == "REGULATION":
            return "OPEN"  # Regulations are open information
        else:
            return "OPEN"  # Default to open for other types

    def _extract_region_from_boe(self, raw_data: dict[str, Any]) -> str:
        """
        Extract region from BOE section/subsection.

        BOE sections contain region information that can be parsed.
        Maps common BOE regional identifiers to Spanish autonomous communities.

        Args:
            raw_data: Raw BOE data

        Returns:
            Region name or empty string if not found
        """
        section = raw_data.get("section", "").strip().lower()
        contracting_authority = raw_data.get("contracting_authority", "").strip().lower()

        # Map of Spanish autonomous communities and common BOE identifiers
        regions = {
            "andalucía": ["andalucía", "andalusia"],
            "aragón": ["aragón", "aragon"],
            "asturias": ["asturias"],
            "illes balears": ["balears", "baleares", "balearic"],
            "país vasco": ["país vasco", "vasco", "basque"],
            "canarias": ["canarias", "canary"],
            "cantabria": ["cantabria"],
            "castilla-la mancha": ["castilla-la mancha", "castilla la mancha"],
            "castilla y león": ["castilla y león", "castilla leon"],
            "cataluña": ["cataluña", "catalonia", "barcelona", "girona", "lleida", "tarragona"],
            "comunidad de madrid": ["madrid", "comunidad de madrid"],
            "comunidad foral de navarra": ["navarra", "navarre"],
            "extremadura": ["extremadura"],
            "galicia": ["galicia", "galician"],
            "la rioja": ["rioja"],
            "región de murcia": ["murcia"],
            "comunitat valenciana": ["valencia", "valenciana", "alicante", "castellón"],
        }

        # Try to match section or authority to a region
        for region, keywords in regions.items():
            for keyword in keywords:
                if keyword in section or keyword in contracting_authority:
                    return region

        # Default to Madrid if nothing found (most BOE entries)
        return "Comunidad de Madrid"


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
