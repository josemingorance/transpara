"""Tests for ETL engine."""
from decimal import Decimal

import pytest
from django.test import TestCase

from apps.contracts.etl.base import BaseNormalizer
from apps.contracts.etl.normalizers import PCSPNormalizer, get_normalizer
from apps.contracts.models import Contract, RawContractData
from apps.providers.models import Provider


class TestNormalizer(BaseNormalizer):
    """Test normalizer implementation."""

    source_platform = "TEST"

    def normalize(self, raw_data):
        """Simple normalize implementation."""
        return {
            "external_id": raw_data.get("id", ""),
            "title": raw_data.get("title", ""),
            "contract_type": "SERVICES",
            "status": "PUBLISHED",
            "budget": self.parse_money(raw_data.get("budget")),
            "contracting_authority": raw_data.get("authority", ""),
            "region": "Test Region",
        }


class TestBaseNormalizer(TestCase):
    """Test BaseNormalizer functionality."""

    def test_parse_date_valid_formats(self):
        """Test date parsing with valid formats."""
        normalizer = TestNormalizer()

        # ISO format
        assert normalizer.parse_date("2024-01-15") is not None
        assert normalizer.parse_date("2024-01-15").day == 15

        # Spanish format
        assert normalizer.parse_date("15/01/2024") is not None
        assert normalizer.parse_date("15/01/2024").day == 15

        # Dash format
        assert normalizer.parse_date("15-01-2024") is not None

    def test_parse_date_invalid(self):
        """Test date parsing with invalid input."""
        normalizer = TestNormalizer()

        assert normalizer.parse_date(None) is None
        assert normalizer.parse_date("") is None
        assert normalizer.parse_date("invalid") is None

    def test_parse_money_numeric(self):
        """Test money parsing with numeric input."""
        normalizer = TestNormalizer()

        assert normalizer.parse_money(1234.56) == Decimal("1234.56")
        assert normalizer.parse_money(1000) == Decimal("1000")
        assert normalizer.parse_money(0) == Decimal("0")

    def test_parse_money_spanish_format(self):
        """Test money parsing with Spanish format."""
        normalizer = TestNormalizer()

        # Spanish format: dot for thousands, comma for decimal
        assert normalizer.parse_money("1.234,56") == Decimal("1234.56")
        assert normalizer.parse_money("1.234.567,89 €") == Decimal("1234567.89")

    def test_parse_money_us_format(self):
        """Test money parsing with US format."""
        normalizer = TestNormalizer()

        # US format: comma for thousands, dot for decimal
        assert normalizer.parse_money("1,234.56") == Decimal("1234.56")
        assert normalizer.parse_money("$1,234.56") == Decimal("1234.56")

    def test_parse_money_invalid(self):
        """Test money parsing with invalid input."""
        normalizer = TestNormalizer()

        assert normalizer.parse_money(None) == Decimal("0")
        assert normalizer.parse_money("") == Decimal("0")

    def test_normalize_contract_type(self):
        """Test contract type normalization."""
        normalizer = TestNormalizer()

        assert normalizer.normalize_contract_type("Construction work") == "WORKS"
        assert normalizer.normalize_contract_type("Cleaning service") == "SERVICES"
        assert normalizer.normalize_contract_type("Material supply") == "SUPPLIES"
        assert normalizer.normalize_contract_type("Mixed contract") == "MIXED"
        assert normalizer.normalize_contract_type("Other") == "OTHER"
        assert normalizer.normalize_contract_type(None) == "OTHER"

    def test_normalize_status(self):
        """Test status normalization."""
        normalizer = TestNormalizer()

        assert normalizer.normalize_status("Published") == "PUBLISHED"
        assert normalizer.normalize_status("Awarded") == "AWARDED"
        assert normalizer.normalize_status("Completed") == "COMPLETED"
        assert normalizer.normalize_status("Cancelled") == "CANCELLED"
        assert normalizer.normalize_status("In progress") == "IN_PROGRESS"
        assert normalizer.normalize_status(None) == "DRAFT"


@pytest.mark.django_db
class TestBaseNormalizerProcessing(TestCase):
    """Test BaseNormalizer record processing."""

    def test_process_raw_record_creates_contract(self):
        """Test processing raw record creates Contract."""
        raw_record = RawContractData.objects.create(
            source_platform="TEST",
            external_id="TEST-001",
            raw_data={
                "id": "TEST-001",
                "title": "Test Contract",
                "budget": "1000.00",
                "authority": "Test Authority",
            },
        )

        normalizer = TestNormalizer()
        contract = normalizer.process_raw_record(raw_record)

        assert contract is not None
        assert contract.external_id == "TEST-001"
        assert contract.title == "Test Contract"
        assert contract.budget == Decimal("1000.00")

        # Check raw record is marked as processed
        raw_record.refresh_from_db()
        assert raw_record.is_processed
        assert raw_record.contract == contract

    def test_process_raw_record_creates_provider(self):
        """Test processing creates Provider when tax_id provided."""
        raw_record = RawContractData.objects.create(
            source_platform="TEST",
            external_id="TEST-002",
            raw_data={
                "id": "TEST-002",
                "title": "Test",
                "budget": "1000",
                "authority": "Test",
                "awarded_to_tax_id": "B12345678",
                "awarded_to_name": "Test Company",
            },
        )

        # Create custom normalizer that includes provider info
        class ProviderNormalizer(TestNormalizer):
            def normalize(self, raw_data):
                result = super().normalize(raw_data)
                result["awarded_to_tax_id"] = raw_data.get("awarded_to_tax_id")
                result["awarded_to_name"] = raw_data.get("awarded_to_name")
                return result

        normalizer = ProviderNormalizer()
        contract = normalizer.process_raw_record(raw_record)

        assert contract.awarded_to is not None
        assert contract.awarded_to.tax_id == "B12345678"
        assert Provider.objects.filter(tax_id="B12345678").exists()


@pytest.mark.django_db
class TestPCSPNormalizer(TestCase):
    """Test PCSP-specific normalizer."""

    def test_normalize_complete_record(self):
        """Test normalizing complete PCSP record."""
        raw_data = {
            "external_id": "PCSP-12345",
            "title": "Construction work",
            "description": "Test description",
            "contract_type": "WORKS",
            "status": "Publicado",
            "budget": "1.234.567,89",
            "awarded_amount": "1.200.000,00",
            "procedure_type": "Open",
            "publication_date": "2024-01-15",
            "deadline": "2024-02-15",
            "award_date": "2024-03-01",
            "contracting_authority": "Ayuntamiento de Madrid",
            "region": "Madrid",
            "province": "Madrid",
            "municipality": "Madrid",
            "source_url": "https://example.com/contract/12345",
        }

        normalizer = PCSPNormalizer()
        normalized = normalizer.normalize(raw_data)

        assert normalized["external_id"] == "PCSP-12345"
        assert normalized["title"] == "Construction work"
        assert normalized["contract_type"] == "WORKS"
        assert normalized["status"] == "PUBLISHED"
        assert normalized["budget"] == Decimal("1234567.89")
        assert normalized["awarded_amount"] == Decimal("1200000.00")
        assert normalized["procedure_type"] == "OPEN"
        assert normalized["contracting_authority"] == "Ayuntamiento de Madrid"

    def test_normalize_minimal_record(self):
        """Test normalizing minimal PCSP record."""
        raw_data = {
            "external_id": "PCSP-MIN",
            "title": "Minimal Contract",
        }

        normalizer = PCSPNormalizer()
        normalized = normalizer.normalize(raw_data)

        assert normalized["external_id"] == "PCSP-MIN"
        assert normalized["title"] == "Minimal Contract"
        assert normalized["budget"] == Decimal("0")


class TestGetNormalizer:
    """Test normalizer registry."""

    def test_get_normalizer_pcsp(self):
        """Test getting PCSP normalizer."""
        normalizer = get_normalizer("PCSP")
        assert normalizer is not None
        assert isinstance(normalizer, PCSPNormalizer)

    def test_get_normalizer_unknown(self):
        """Test getting unknown normalizer returns None."""
        normalizer = get_normalizer("UNKNOWN")
        assert normalizer is None
