"""
External API integration for provider data enrichment.

Provides classes for querying BOE and PCSP APIs to enrich provider data
with website, industry, founding year, and other business information.
"""

import logging
import re
from typing import Any, Optional
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)


class APIEnricher:
    """Base class for API enrichers."""

    TIMEOUT = 10
    MAX_RETRIES = 2

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.session = requests.Session()
        self._setup_session()

    def _setup_session(self) -> None:
        """Configure session headers."""
        self.session.headers.update({
            "User-Agent": "PublicWorks-AI/1.0 (+https://github.com/)"
        })

    def search_provider(self, tax_id: str, company_name: str) -> dict[str, Any]:
        """Search for provider information. Override in subclasses."""
        raise NotImplementedError


class PCSPEnricher(APIEnricher):
    """
    Enrich provider data from PCSP (Plataforma de Contratación Sector Público).

    PCSP is the official Spanish public procurement platform with extensive
    company and contract data.
    """

    BASE_URL = "https://contrataciondelsectorpublico.gob.es/wlpl/rest"

    def search_provider(self, tax_id: str, company_name: str) -> dict[str, Any]:
        """Search PCSP for provider information."""
        # Try tax ID first (more precise)
        if tax_id:
            result = self._search_by_nif(tax_id)
            if result.get("found"):
                return result

        # Fall back to name search
        if company_name:
            result = self._search_by_name(company_name)
            if result.get("found"):
                return result

        return {"found": False, "source": "pcsp"}

    def _search_by_nif(self, nif: str) -> dict[str, Any]:
        """Search by company NIF/CIF."""
        # Clean NIF format
        nif = nif.upper().strip()

        try:
            endpoint = f"{self.BASE_URL}/empresas/search"
            params = {
                "query": f"nif:{nif}",
                "page": "1",
                "pageSize": "5"
            }

            response = self.session.get(
                endpoint,
                params=params,
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            if data.get("items"):
                return self._extract_company_info(data["items"][0])

            return {"found": False, "source": "pcsp", "nif": nif}

        except requests.RequestException as e:
            if self.verbose:
                logger.warning(f"PCSP NIF search failed ({nif}): {e}")
            return {"found": False, "error": str(e), "source": "pcsp"}

    def _search_by_name(self, name: str) -> dict[str, Any]:
        """Search by company name."""
        try:
            endpoint = f"{self.BASE_URL}/empresas/search"
            params = {
                "query": f"nombre:{name}",
                "page": "1",
                "pageSize": "3"
            }

            response = self.session.get(
                endpoint,
                params=params,
                timeout=self.TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            if data.get("items"):
                return self._extract_company_info(data["items"][0])

            return {"found": False, "source": "pcsp", "name": name}

        except requests.RequestException as e:
            if self.verbose:
                logger.warning(f"PCSP name search failed ({name}): {e}")
            return {"found": False, "error": str(e), "source": "pcsp"}

    def _extract_company_info(self, item: dict[str, Any]) -> dict[str, Any]:
        """Extract structured company information from PCSP response."""
        result: dict[str, Any] = {"found": True, "source": "pcsp"}

        # Website
        if website := item.get("website"):
            result["website"] = self._normalize_url(website)

        # Email
        if email := item.get("email"):
            result["email"] = email.lower().strip()

        # Phone
        if phone := item.get("phone"):
            result["phone"] = self._normalize_phone(phone)

        # Industry/Sector
        if sector := item.get("sector") or item.get("activity"):
            result["industry"] = sector

        # Company size
        if size := item.get("size") or item.get("num_employees"):
            result["company_size"] = str(size)

        # Founding year
        if year := self._extract_year(item.get("founded_year") or item.get("year")):
            result["founded_year"] = year

        # Legal name
        if legal_name := item.get("legal_name") or item.get("name"):
            result["legal_name"] = legal_name

        return result

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Normalize URL to proper format."""
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        return url

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """Extract and normalize phone number."""
        # Remove common separators
        phone = re.sub(r"[\s\-\(\)]+", "", phone)
        return phone

    @staticmethod
    def _extract_year(year_input: Optional[Any]) -> Optional[int]:
        """Extract valid founding year from various formats."""
        if not year_input:
            return None

        try:
            year_str = str(year_input).strip()
            year = int(year_str[-4:])  # Get last 4 digits

            # Validate year is reasonable
            if 1800 <= year <= 2100:
                return year
        except (ValueError, TypeError, IndexError):
            pass

        return None


class BOEEnricher(APIEnricher):
    """
    Enrich provider data from BOE (Boletín Oficial del Estado).

    BOE publishes official government contracts and notices. This enricher
    searches BOE for company information and public contract history.
    """

    BASE_URL = "https://www.boe.es"

    def search_provider(self, tax_id: str, company_name: str) -> dict[str, Any]:
        """Search BOE for provider information."""
        # BOE doesn't provide structured API, but we can search for mentions
        # Focus on PCSP instead for structured data
        return {"found": False, "source": "boe", "note": "BOE API not fully implemented"}


class LinkedDataEnricher(APIEnricher):
    """
    Enrich provider data from Linked Data sources.

    Uses public RDF/Linked Data endpoints to enrich company information.
    """

    def search_provider(self, tax_id: str, company_name: str) -> dict[str, Any]:
        """Search linked data sources for company information."""
        # This would integrate with dbpedia, wikidata, etc.
        return {"found": False, "source": "linked_data", "note": "Not yet implemented"}


class EnrichmentPipeline:
    """
    Coordinate enrichment from multiple sources.

    Tries sources in priority order and combines results.
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.enrichers = [
            PCSPEnricher(verbose=verbose),
            # LinkedDataEnricher(verbose=verbose),
            # BOEEnricher(verbose=verbose),
        ]

    def enrich(self, tax_id: str, company_name: str) -> dict[str, Any]:
        """Enrich from multiple sources, returning best result."""
        for enricher in self.enrichers:
            try:
                result = enricher.search_provider(tax_id, company_name)
                if result.get("found"):
                    return result
            except Exception as e:
                if self.verbose:
                    logger.warning(f"Enricher error: {e}")
                continue

        return {"found": False, "sources_tried": [e.__class__.__name__ for e in self.enrichers]}
