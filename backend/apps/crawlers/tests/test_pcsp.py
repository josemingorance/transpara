"""Tests for PCSP crawler."""
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

import pytest
from django.test import TestCase

from apps.crawlers.base import CrawlerException
from apps.crawlers.implementations.pcsp import PCSPCrawler


class TestPCSPCrawler(TestCase):
    """Test PCSP crawler functionality."""

    def test_crawler_attributes(self):
        """Test crawler has correct attributes."""
        crawler = PCSPCrawler()

        assert crawler.name == "pcsp"
        assert crawler.source_platform == "PCSP"
        assert "contrataciondelestado" in crawler.source_url

    def test_services_initialized(self):
        """Test that all services are properly initialized."""
        crawler = PCSPCrawler()
        
        # Check utilities
        assert crawler.date_handler is not None
        assert crawler.money_handler is not None
        assert crawler.region_extractor is not None
        
        # Check services
        assert crawler.discovery_service is not None
        assert crawler.parsing_service is not None
        assert crawler.fetch_service is not None

    def test_parse_success(self):
        """Test parsing valid contract data."""
        crawler = PCSPCrawler()
        
        raw_data = [
            {
                "id": "PCSP-001",
                "title": "Construction work",
                "budget": 1000000.00,
                "contracting_authority": "Ayuntamiento de Madrid",
                "publicationDate": "2025-11-20",
            },
            {
                "id": "PCSP-002",
                "title": "Consulting service",
                "budget": 500000.00,
                "contracting_authority": "Ministerio",
                "publicationDate": "2025-11-21",
            }
        ]
        
        contracts = crawler.parse(raw_data)

        assert len(contracts) == 2
        assert contracts[0]["external_id"] == "PCSP-001"
        assert contracts[1]["external_id"] == "PCSP-002"

    def test_parse_empty_list(self):
        """Test parsing empty list."""
        crawler = PCSPCrawler()
        contracts = crawler.parse([])

        assert len(contracts) == 0

    def test_parse_dict_wrapper(self):
        """Test parsing with dict wrapper."""
        crawler = PCSPCrawler()
        
        raw_data = {
            "contracts": [
                {
                    "id": "PCSP-001",
                    "title": "Test Contract",
                    "budget": 1000000.00,
                }
            ]
        }
        
        contracts = crawler.parse(raw_data)
        assert len(contracts) == 1

    def test_date_handler_parse(self):
        """Test date handler parsing."""
        crawler = PCSPCrawler()
        
        # Spanish format
        assert crawler.date_handler.parse_to_iso("29/11/2025") == "2025-11-29"
        
        # ISO format
        assert crawler.date_handler.parse_to_iso("2025-11-29") == "2025-11-29"
        
        # Invalid
        assert crawler.date_handler.parse_to_iso("invalid") is None

    def test_money_handler_parse(self):
        """Test money handler parsing."""
        crawler = PCSPCrawler()
        
        # Spanish format
        result = crawler.money_handler.parse_decimal("1.234,56")
        assert result == Decimal("1234.56")
        
        # US format
        result = crawler.money_handler.parse_decimal("1,234.56")
        assert result == Decimal("1234.56")
        
        # With currency symbol
        result = crawler.money_handler.parse_decimal("€ 1.000,00")
        assert result == Decimal("1000.00")
        
        # Invalid
        assert crawler.money_handler.parse_decimal("invalid") is None

    def test_region_extractor(self):
        """Test region extraction."""
        crawler = PCSPCrawler()
        
        assert crawler.region_extractor.extract_region("Ayuntamiento de Barcelona") == "Cataluña"
        assert crawler.region_extractor.extract_region("Junta de Andalucía") == "Andalucía"
        assert crawler.region_extractor.extract_region("Comunidad de Madrid") == "Comunidad de Madrid"
        assert crawler.region_extractor.extract_region("Unknown Authority") == ""

    def test_parsing_service_contract_type_inference(self):
        """Test contract type inference in parsing service."""
        crawler = PCSPCrawler()
        
        assert crawler.parsing_service._infer_contract_type("", "Construction work") == "WORKS"
        assert crawler.parsing_service._infer_contract_type("", "Cleaning service") == "SERVICES"
        assert crawler.parsing_service._infer_contract_type("", "Equipment supply") == "SUPPLIES"
        assert crawler.parsing_service._infer_contract_type("", "Unknown") == "OTHER"

    def test_parsing_service_status_inference(self):
        """Test status inference in parsing service."""
        crawler = PCSPCrawler()
        
        assert crawler.parsing_service._infer_status({"status": "PUB"}) == "PUBLISHED"
        assert crawler.parsing_service._infer_status({"status": "RES"}) == "AWARDED"
        assert crawler.parsing_service._infer_status({"status": "EJE"}) == "IN_PROGRESS"
        assert crawler.parsing_service._infer_status({"status": "CAN"}) == "CANCELLED"

    def test_parsing_service_procedure_type_mapping(self):
        """Test procedure type mapping in parsing service."""
        crawler = PCSPCrawler()
        
        assert crawler.parsing_service._map_procedure_type("1") == "OPEN"
        assert crawler.parsing_service._map_procedure_type("2") == "RESTRICTED"
        assert crawler.parsing_service._map_procedure_type("3") == "NEGOTIATED"
        assert crawler.parsing_service._map_procedure_type("abierto") == "OPEN"

    def test_fetch_raw_uses_service(self):
        """Test fetch_raw delegates to fetch service."""
        crawler = PCSPCrawler()
        
        # Mock the fetch_service.fetch_all method
        with patch.object(crawler.fetch_service, 'fetch_all', return_value=[{"id": "001", "title": "Test"}]):
            result = crawler.fetch_raw()
            
            assert len(result) == 1
            crawler.fetch_service.fetch_all.assert_called_once()

    def test_fetch_raw_raises_on_empty_data(self):
        """Test that fetch_raw raises exception when no data available."""
        crawler = PCSPCrawler()

        # Mock fetch_service to return empty list
        crawler.fetch_service = Mock()
        crawler.fetch_service.fetch_all.return_value = []

        # Should raise CrawlerException
        with pytest.raises(CrawlerException):
            crawler.fetch_raw()


@pytest.mark.django_db
class TestPCSPCrawlerIntegration(TestCase):
    """Integration tests for PCSP crawler."""

    def test_full_crawler_with_real_data(self):
        """Test complete crawler execution with real data."""
        crawler = PCSPCrawler()

        # Mock fetch_service to return real data structure
        # Use a title that will be correctly parsed as SERVICES
        mock_data = [
            {
                "id": "PCSP-TEST-001",
                "title": "Consulting service contract",
                "status": "PUBLISHED",
                "budget": 100000.00,
                "contracting_authority": "Test Authority",
                "procedure_type": "OPEN",
            }
        ]
        crawler.fetch_service = Mock()
        crawler.fetch_service.fetch_all.return_value = mock_data

        run = crawler.run_crawler()

        assert run.status == "SUCCESS"
        assert run.records_found == 1
        assert run.records_created == 1

        # Verify data was saved
        from apps.contracts.models import RawContractData

        assert RawContractData.objects.filter(source_platform="PCSP").count() == 1

    def test_parsing_service_integration(self):
        """Test parsing service integration."""
        crawler = PCSPCrawler()
        
        raw_contracts = [
            {
                "id": "TEST-001",
                "title": "Infrastructure work",
                "description": "Test description",
                "budget_without_taxes": "1.000.000,00",
                "contracting_authority": "Ayuntamiento de Barcelona",
                "first_publication_date": "2025-11-20",
                "procedure_type": "1",
                "status": "PUB",
            }
        ]
        
        parsed = crawler.parsing_service.parse_contracts(raw_contracts)
        
        assert len(parsed) == 1
        assert parsed[0]["external_id"] == "TEST-001"
        assert parsed[0]["contract_type"] == "WORKS"
        assert parsed[0]["region"] == "Cataluña"
        assert parsed[0]["status"] == "PUBLISHED"
        assert parsed[0]["procedure_type"] == "OPEN"
        assert parsed[0]["budget"] == 1000000.00
