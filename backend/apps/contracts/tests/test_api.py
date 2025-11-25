"""Tests for contracts API."""
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.contracts.models import Contract, ContractAmendment
from apps.providers.models import Provider


@pytest.mark.django_db
class TestContractAPI(APITestCase):
    """Test contract API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.provider = Provider.objects.create(
            name="Test Provider",
            tax_id="B12345678",
        )

        self.contract = Contract.objects.create(
            external_id="TEST-001",
            title="Test Contract",
            contract_type="SERVICES",
            status="AWARDED",
            budget=Decimal("100000"),
            awarded_amount=Decimal("105000"),
            procedure_type="OPEN",
            publication_date=timezone.now().date(),
            region="Madrid",
            contracting_authority="Test Authority",
            source_platform="TEST",
            awarded_to=self.provider,
            risk_score=Decimal("45.5"),
        )

    def test_list_contracts(self):
        """Test listing contracts."""
        url = reverse("contract-list")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["external_id"] == "TEST-001"

    def test_retrieve_contract(self):
        """Test retrieving contract detail."""
        url = reverse("contract-detail", kwargs={"pk": self.contract.pk})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["external_id"] == "TEST-001"
        assert response.data["title"] == "Test Contract"
        assert "risk_score" in response.data

    def test_filter_by_type(self):
        """Test filtering by contract type."""
        url = reverse("contract-list")
        response = self.client.get(url, {"contract_type": "SERVICES"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

        response = self.client.get(url, {"contract_type": "WORKS"})
        assert response.data["count"] == 0

    def test_filter_by_risk(self):
        """Test filtering by risk score."""
        url = reverse("contract-list")
        response = self.client.get(url, {"risk_score_min": 40})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

        response = self.client.get(url, {"risk_score_min": 50})
        assert response.data["count"] == 0

    def test_search_contracts(self):
        """Test search functionality."""
        url = reverse("contract-list")
        response = self.client.get(url, {"search": "Test Contract"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

        response = self.client.get(url, {"search": "Nonexistent"})
        assert response.data["count"] == 0

    def test_contract_stats(self):
        """Test contract statistics endpoint."""
        url = reverse("contract-stats")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_contracts"] == 1
        assert Decimal(response.data["total_budget"]) == Decimal("100000")

    def test_high_risk_filter(self):
        """Test high risk filter."""
        # Create high-risk contract
        Contract.objects.create(
            external_id="TEST-HIGH",
            title="High Risk Contract",
            contract_type="WORKS",
            status="AWARDED",
            budget=Decimal("200000"),
            region="Madrid",
            contracting_authority="Test Authority",
            source_platform="TEST",
            risk_score=Decimal("85"),
        )

        url = reverse("contract-list")
        response = self.client.get(url, {"high_risk": "true"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["external_id"] == "TEST-HIGH"

    def test_contract_amendments(self):
        """Test retrieving contract amendments."""
        # Create amendment
        ContractAmendment.objects.create(
            contract=self.contract,
            amendment_type="BUDGET_INCREASE",
            description="Budget increase",
            previous_amount=Decimal("100000"),
            new_amount=Decimal("105000"),
            amendment_date=timezone.now().date(),
        )

        url = reverse("contract-amendments", kwargs={"pk": self.contract.pk})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["amendment_type"] == "BUDGET_INCREASE"

    def test_by_region(self):
        """Test grouping by region."""
        url = reverse("contract-by-region")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["region"] == "Madrid"
        assert response.data[0]["count"] == 1

    def test_by_type(self):
        """Test grouping by type."""
        url = reverse("contract-by-type")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["contract_type"] == "SERVICES"
        assert response.data[0]["count"] == 1


@pytest.mark.django_db
class TestContractPagination(APITestCase):
    """Test pagination on contract lists."""

    def setUp(self):
        """Create multiple contracts."""
        for i in range(25):
            Contract.objects.create(
                external_id=f"TEST-{i:03d}",
                title=f"Contract {i}",
                contract_type="SERVICES",
                status="PUBLISHED",
                budget=Decimal("100000"),
                region="Madrid",
                contracting_authority="Test Authority",
                source_platform="TEST",
            )

    def test_default_pagination(self):
        """Test default pagination (100 items per page)."""
        url = reverse("contract-list")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 25
        assert len(response.data["results"]) == 25

    def test_custom_page_size(self):
        """Test custom page size."""
        url = reverse("contract-list")
        response = self.client.get(url, {"page_size": 10})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 10


@pytest.mark.django_db
class TestContractOrdering(APITestCase):
    """Test ordering of contracts."""

    def setUp(self):
        """Create contracts with different values."""
        Contract.objects.create(
            external_id="TEST-LOW",
            title="Low Budget",
            contract_type="SERVICES",
            status="PUBLISHED",
            budget=Decimal("10000"),
            region="Madrid",
            contracting_authority="Test Authority",
            source_platform="TEST",
            risk_score=Decimal("20"),
        )

        Contract.objects.create(
            external_id="TEST-HIGH",
            title="High Budget",
            contract_type="SERVICES",
            status="PUBLISHED",
            budget=Decimal("500000"),
            region="Madrid",
            contracting_authority="Test Authority",
            source_platform="TEST",
            risk_score=Decimal("80"),
        )

    def test_order_by_budget(self):
        """Test ordering by budget."""
        url = reverse("contract-list")
        response = self.client.get(url, {"ordering": "budget"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["external_id"] == "TEST-LOW"

        response = self.client.get(url, {"ordering": "-budget"})
        assert response.data["results"][0]["external_id"] == "TEST-HIGH"

    def test_order_by_risk(self):
        """Test ordering by risk score."""
        url = reverse("contract-list")
        response = self.client.get(url, {"ordering": "-risk_score"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"][0]["external_id"] == "TEST-HIGH"
