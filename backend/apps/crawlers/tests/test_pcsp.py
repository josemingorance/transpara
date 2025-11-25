"""Tests for PCSP crawler."""
from unittest.mock import Mock, patch

import pytest
from django.test import TestCase

from apps.crawlers.base import CrawlerException
from apps.crawlers.implementations.pcsp import PCSPCrawler


SAMPLE_HTML = """
<html>
    <body>
        <div class="contract-item">
            <h3 class="title">Obra de construcción de infraestructura</h3>
            <span class="budget">1.234.567,89 €</span>
            <span class="deadline">2024-12-31</span>
            <div class="authority">Ayuntamiento de Madrid</div>
            <a class="view-details" href="/contract/12345">Ver detalles</a>
        </div>
        <div class="contract-item">
            <h3 class="title">Servicio de consultoría técnica</h3>
            <span class="budget">500.000,00 €</span>
            <span class="deadline">2024-11-30</span>
            <div class="authority">Ministerio de Fomento</div>
            <a class="view-details" href="/contract/67890">Ver detalles</a>
        </div>
    </body>
</html>
"""


class TestPCSPCrawler(TestCase):
    """Test PCSP crawler functionality."""

    def test_crawler_attributes(self):
        """Test crawler has correct attributes."""
        crawler = PCSPCrawler()

        assert crawler.name == "pcsp"
        assert crawler.source_platform == "PCSP"
        assert "contrataciondelestado" in crawler.source_url

    def test_parse_success(self):
        """Test parsing valid HTML."""
        crawler = PCSPCrawler()
        contracts = crawler.parse(SAMPLE_HTML)

        assert len(contracts) == 2

        # Check first contract
        assert contracts[0]["external_id"] == "PCSP-12345"
        assert "construcción" in contracts[0]["title"].lower()
        assert contracts[0]["budget"] == 1234567.89
        assert contracts[0]["contracting_authority"] == "Ayuntamiento de Madrid"
        assert contracts[0]["contract_type"] == "WORKS"

        # Check second contract
        assert contracts[1]["external_id"] == "PCSP-67890"
        assert "consultoría" in contracts[1]["title"].lower()
        assert contracts[1]["budget"] == 500000.00
        assert contracts[1]["contract_type"] == "SERVICES"

    def test_parse_empty_html(self):
        """Test parsing empty HTML."""
        crawler = PCSPCrawler()
        contracts = crawler.parse("<html><body></body></html>")

        assert len(contracts) == 0

    def test_parse_invalid_html(self):
        """Test parsing invalid HTML raises exception."""
        crawler = PCSPCrawler()

        # Should not raise, just return empty list
        contracts = crawler.parse("invalid html")
        assert len(contracts) == 0

    def test_parse_budget_formats(self):
        """Test budget parsing with different formats."""
        crawler = PCSPCrawler()

        # Spanish format with dots and comma
        assert crawler._parse_budget("1.234.567,89 €") == 1234567.89

        # Simple format
        assert crawler._parse_budget("500.000,00 €") == 500000.00

        # Invalid format
        assert crawler._parse_budget("invalid") is None
        assert crawler._parse_budget("") is None

    def test_infer_type_works(self):
        """Test contract type inference for works."""
        crawler = PCSPCrawler()

        assert crawler._infer_type("Obra de construcción") == "WORKS"
        assert crawler._infer_type("Infraestructura vial") == "WORKS"

    def test_infer_type_services(self):
        """Test contract type inference for services."""
        crawler = PCSPCrawler()

        assert crawler._infer_type("Servicio de limpieza") == "SERVICES"
        assert crawler._infer_type("Consultoría técnica") == "SERVICES"
        assert crawler._infer_type("Asistencia técnica") == "SERVICES"

    def test_infer_type_supplies(self):
        """Test contract type inference for supplies."""
        crawler = PCSPCrawler()

        assert crawler._infer_type("Suministro de material") == "SUPPLIES"
        assert crawler._infer_type("Equipos informáticos") == "SUPPLIES"

    def test_infer_type_other(self):
        """Test contract type inference for unknown types."""
        crawler = PCSPCrawler()

        assert crawler._infer_type("Contrato mixto") == "OTHER"
        assert crawler._infer_type("Algo desconocido") == "OTHER"

    def test_parse_contract_row_missing_elements(self):
        """Test parsing row with missing elements."""
        from bs4 import BeautifulSoup

        crawler = PCSPCrawler()

        # Missing required elements
        html = '<div class="contract-item"><h3 class="title">Title</h3></div>'
        soup = BeautifulSoup(html, "lxml")
        row = soup.find("div", class_="contract-item")

        result = crawler._parse_contract_row(row)

        assert result is None

    @patch("apps.crawlers.base.requests.Session.get")
    def test_fetch_raw_called(self, mock_get):
        """Test fetch_raw makes HTTP request."""
        mock_response = Mock()
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        crawler = PCSPCrawler()
        result = crawler.fetch_raw()

        assert result == SAMPLE_HTML
        mock_get.assert_called_once()


@pytest.mark.django_db
class TestPCSPCrawlerIntegration(TestCase):
    """Integration tests for PCSP crawler."""

    @patch("apps.crawlers.base.requests.Session.get")
    def test_full_crawler_run(self, mock_get):
        """Test complete crawler execution."""
        mock_response = Mock()
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        crawler = PCSPCrawler()
        run = crawler.run_crawler()

        assert run.status == "SUCCESS"
        assert run.records_found == 2
        assert run.records_created == 2

        # Verify data was saved
        from apps.contracts.models import RawContractData

        assert RawContractData.objects.count() == 2
        assert RawContractData.objects.filter(source_platform="PCSP").count() == 2
