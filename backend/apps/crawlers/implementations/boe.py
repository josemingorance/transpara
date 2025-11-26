"""
BOE (Boletín Oficial del Estado) crawler.

Collects publication data from Spain's official state bulletin.
Processes the JSON API structure to extract all items from the daily bulletin.
"""
from datetime import datetime

import requests

from apps.crawlers.base import CrawlerException, BaseCrawler
from apps.crawlers.registry import register_crawler


@register_crawler
class BOECrawler(BaseCrawler):
    """
    Crawler for BOE API platform.

    Extracts all items (contracts, announcements, regulations, etc.)
    from the official state bulletin API using JSON format.
    """

    name = "boe"
    source_platform = "BOE"
    source_url = "https://www.boe.es/datosabiertos/api/boe/sumario"

    def fetch_raw(self) -> dict:
        """
        Fetch JSON data from BOE API for today.

        Returns:
            JSON response as dictionary

        Raises:
            CrawlerException: If request fails
        """
        try:
            today = datetime.now().strftime("%Y%m%d")
            url = f"{self.source_url}/{today}"

            headers = self.session.headers.copy()
            headers["Accept"] = "application/json"

            response = self.session.get(url, timeout=30, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise CrawlerException(f"Failed to fetch JSON: {e}")
        except ValueError as e:
            raise CrawlerException(f"Invalid JSON response: {e}")

    def parse(self, raw: dict) -> list[dict]:
        """
        Parse JSON to extract all items from BOE.

        Navigates the nested structure:
        - data.sumario.issues[] (daily publications)
          - section[] (sections like I. Disposiciones, II. Autoridades, etc.)
            - department[] (government departments)
              - subsection[] (subsections)
                - item or item[] (actual publications/documents)

        Args:
            raw: JSON response from BOE API

        Returns:
            List of item dictionaries
        """
        try:
            items = []

            if not isinstance(raw, dict):
                return items

            data = raw.get("data", {})
            sumario = data.get("sumario", {})
            issues = sumario.get("diario", [])

            for issue in issues:
                sections = issue.get("seccion", [])
                if not isinstance(sections, list):
                    sections = [sections]

                for section in sections:
                    section_name = section.get("nombre", "")
                    departments = section.get("departamento", [])
                    if not isinstance(departments, list):
                        departments = [departments]

                    for department in departments:
                        dept_name = department.get("nombre", "")
                        subsections = department.get("epigrafe", [])
                        if not isinstance(subsections, list):
                            subsections = [subsections]

                        for subsection in subsections:
                            subsection_name = subsection.get("nombre", "")
                            item_list = subsection.get("item", [])

                            if not isinstance(item_list, list):
                                item_list = [item_list]

                            for item in item_list:
                                try:
                                    parsed = self._parse_item(
                                        item, section_name, dept_name, subsection_name
                                    )
                                    if parsed:
                                        items.append(parsed)
                                except Exception as e:
                                    self.logger.warning(f"Failed to parse item: {e}")
                                    continue

            return items

        except Exception as e:
            raise CrawlerException(f"Failed to parse JSON: {e}")

    def _parse_item(
        self, item: dict, section: str, department: str, subsection: str
    ) -> dict | None:
        """
        Parse individual BOE item.

        Args:
            item: Dictionary with item data
            section: Section name (e.g., "I. Disposiciones generales")
            department: Department/ministry name
            subsection: Subsection/category name

        Returns:
            Item dictionary or None if parsing fails
        """
        try:
            title = item.get("titulo", "").strip()
            identifier = item.get("identificador", "").strip()
            url_html = item.get("url_html", "").strip()

            if not title or not identifier:
                return None

            return {
                "external_id": identifier,
                "title": title,
                "contracting_authority": department,
                "source_url": url_html if url_html.startswith("http") else f"https://www.boe.es{url_html}",
                "section": section,
                "subsection": subsection,
                "item_type": self._infer_item_type(section, subsection),
                "publication_date": datetime.now().strftime("%Y-%m-%d"),
            }

        except Exception as e:
            self.logger.debug(f"Item parsing error: {e}")
            return None

    @staticmethod
    def _infer_item_type(section: str, subsection: str) -> str:
        """
        Infer item type based on section and subsection names.

        Args:
            section: Section name
            subsection: Subsection name

        Returns:
            Item type classification
        """
        section_lower = section.lower()
        subsection_lower = subsection.lower()

        if "contratación" in section_lower or "contratación" in subsection_lower:
            return "CONTRACT"
        elif "anuncio" in subsection_lower or "licitación" in subsection_lower:
            return "ANNOUNCEMENT"
        elif "disposicion" in section_lower or "decreto" in subsection_lower:
            return "REGULATION"
        elif "autoridad" in section_lower:
            return "AUTHORITY"
        else:
            return "OTHER"