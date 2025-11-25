"""
PCSP (Plataforma de Contratación del Sector Público) crawler.

Collects contract data from Spain's national public procurement platform.
Note: This is a simplified example. Real implementation would need
to handle pagination, authentication, rate limiting, etc.
"""
from typing import Any

from bs4 import BeautifulSoup

from apps.crawlers.base import CrawlerException, HTMLCrawler
from apps.crawlers.registry import register_crawler


@register_crawler
class PCSPCrawler(HTMLCrawler):
    """
    Crawler for PCSP platform.

    Extracts contract information from the national
    public procurement website.
    """

    name = "pcsp"
    source_platform = "PCSP"
    source_url = "https://contrataciondelestado.es/wps/portal/licitaciones"

    def parse(self, raw: str) -> list[dict]:
        """
        Parse HTML to extract contract data.

        Args:
            raw: HTML string from PCSP

        Returns:
            List of contract dictionaries

        Raises:
            CrawlerException: If parsing fails
        """
        try:
            soup = BeautifulSoup(raw, "lxml")
            contracts = []

            # This is a simplified example
            # Real implementation would parse actual PCSP structure
            contract_rows = soup.find_all("div", class_="contract-item")

            for row in contract_rows:
                try:
                    contract = self._parse_contract_row(row)
                    if contract:
                        contracts.append(contract)
                except Exception as e:
                    self.logger.warning(f"Failed to parse row: {e}")
                    continue

            return contracts

        except Exception as e:
            raise CrawlerException(f"Failed to parse HTML: {e}")

    def _parse_contract_row(self, row: Any) -> dict | None:
        """
        Parse individual contract row.

        Args:
            row: BeautifulSoup element

        Returns:
            Contract dictionary or None if parsing fails
        """
        try:
            # Example structure - adjust to real PCSP format
            title_elem = row.find("h3", class_="title")
            budget_elem = row.find("span", class_="budget")
            deadline_elem = row.find("span", class_="deadline")
            authority_elem = row.find("div", class_="authority")
            link_elem = row.find("a", class_="view-details")

            if not all([title_elem, budget_elem, authority_elem, link_elem]):
                return None

            # Extract external ID from link
            link = link_elem.get("href", "")
            external_id = link.split("/")[-1] if link else None

            if not external_id:
                return None

            return {
                "external_id": f"PCSP-{external_id}",
                "title": title_elem.text.strip(),
                "budget": self._parse_budget(budget_elem.text),
                "deadline": deadline_elem.text.strip() if deadline_elem else None,
                "contracting_authority": authority_elem.text.strip(),
                "source_url": f"https://contrataciondelestado.es{link}",
                "contract_type": self._infer_type(title_elem.text),
            }

        except Exception as e:
            self.logger.debug(f"Row parsing error: {e}")
            return None

    def _parse_budget(self, budget_text: str) -> float | None:
        """
        Parse budget string to float.

        Args:
            budget_text: Budget string (e.g., "1.234.567,89 €")

        Returns:
            Budget as float or None
        """
        try:
            # Remove currency symbols and spaces
            cleaned = budget_text.replace("€", "").replace(" ", "").strip()
            # Handle Spanish number format (. for thousands, , for decimal)
            cleaned = cleaned.replace(".", "").replace(",", ".")
            return float(cleaned)
        except (ValueError, AttributeError):
            return None

    def _infer_type(self, title: str) -> str:
        """
        Infer contract type from title.

        Args:
            title: Contract title

        Returns:
            Contract type (WORKS, SERVICES, SUPPLIES, OTHER)
        """
        title_lower = title.lower()

        if any(word in title_lower for word in ["obra", "construcción", "infraestructura"]):
            return "WORKS"
        elif any(word in title_lower for word in ["servicio", "asistencia", "consultoría"]):
            return "SERVICES"
        elif any(word in title_lower for word in ["suministro", "material", "equipo"]):
            return "SUPPLIES"
        else:
            return "OTHER"
