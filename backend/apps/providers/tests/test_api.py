"""Tests for providers API."""
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.contracts.models import Contract
from apps.providers.models import Provider, ProviderAlert


@pytest.mark.django_db
class TestProviderAPI(APITestCase):
    """Test provider API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.provider = Provider.objects.create(
            name="Test Provider",
            tax_id="B12345678",
            region="Madrid",
            industry="Construction",
            total_contracts=10,
            total_awarded_amount=Decimal("1000000"),
            success_rate=Decimal("45.5"),
            risk_score=Decimal("35.5"),
        )

    def test_list_providers(self):
        """Test listing providers."""
        url = reverse("provider-list")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["tax_id"] == "B12345678"

    def test_retrieve_provider(self):
        """Test retrieving provider detail."""
        url = reverse("provider-detail", kwargs={"pk": self.provider.pk})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Provider"
        assert response.data["tax_id"] == "B12345678"
        assert "risk_score" in response.data

    def test_filter_by_region(self):
        """Test filtering by region."""
        url = reverse("provider-list")
        response = self.client.get(url, {"region": "Madrid"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

        response = self.client.get(url, {"region": "Barcelona"})
        assert response.data["count"] == 0

    def test_filter_by_flagged(self):
        """Test filtering by flagged status."""
        # Create flagged provider
        Provider.objects.create(
            name="Flagged Provider",
            tax_id="B87654321",
            is_flagged=True,
        )

        url = reverse("provider-list")
        response = self.client.get(url, {"is_flagged": "true"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1
        assert response.data["results"][0]["tax_id"] == "B87654321"

    def test_search_providers(self):
        """Test search functionality."""
        url = reverse("provider-list")
        response = self.client.get(url, {"search": "Test Provider"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

        response = self.client.get(url, {"search": "B12345678"})
        assert response.data["count"] == 1

        response = self.client.get(url, {"search": "Nonexistent"})
        assert response.data["count"] == 0

    def test_provider_stats(self):
        """Test provider statistics endpoint."""
        url = reverse("provider-stats")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_providers"] == 1
        assert response.data["total_contracts"] == 10

    def test_provider_contracts(self):
        """Test retrieving provider's contracts."""
        # Create contracts for provider
        for i in range(3):
            Contract.objects.create(
                external_id=f"TEST-{i}",
                title=f"Contract {i}",
                contract_type="SERVICES",
                status="AWARDED",
                budget=Decimal("100000"),
                region="Madrid",
                contracting_authority="Test Authority",
                source_platform="TEST",
                awarded_to=self.provider,
            )

        url = reverse("provider-contracts", kwargs={"pk": self.provider.pk})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

    def test_provider_alerts(self):
        """Test retrieving provider's alerts."""
        # Create alerts
        ProviderAlert.objects.create(
            provider=self.provider,
            severity="HIGH",
            alert_type="OVERPRICING",
            title="Test Alert",
            description="Test description",
        )

        url = reverse("provider-alerts", kwargs={"pk": self.provider.pk})
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["severity"] == "HIGH"

    def test_by_region(self):
        """Test grouping by region."""
        url = reverse("provider-by-region")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["region"] == "Madrid"

    def test_by_industry(self):
        """Test grouping by industry."""
        url = reverse("provider-by-industry")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["industry"] == "Construction"


@pytest.mark.django_db
class TestProviderAlertAPI(APITestCase):
    """Test provider alert API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.provider = Provider.objects.create(
            name="Test Provider",
            tax_id="B12345678",
        )

        self.alert = ProviderAlert.objects.create(
            provider=self.provider,
            severity="CRITICAL",
            alert_type="CORRUPTION_INDICATORS",
            title="Critical Alert",
            description="Test description",
            is_resolved=False,
        )

    def test_list_alerts(self):
        """Test listing alerts."""
        url = reverse("provider-alert-list")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

    def test_filter_by_severity(self):
        """Test filtering by severity."""
        url = reverse("provider-alert-list")
        response = self.client.get(url, {"severity": "CRITICAL"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] == 1

        response = self.client.get(url, {"severity": "LOW"})
        assert response.data["count"] == 0

    def test_unresolved_alerts(self):
        """Test unresolved alerts endpoint."""
        url = reverse("provider-alert-unresolved")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

        # Resolve alert
        self.alert.is_resolved = True
        self.alert.save()

        response = self.client.get(url)
        assert len(response.data["results"]) == 0

    def test_critical_alerts(self):
        """Test critical alerts endpoint."""
        url = reverse("provider-alert-critical")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["severity"] == "CRITICAL"
