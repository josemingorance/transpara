"""Tests for analytics API."""
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.contracts.models import Contract
from apps.providers.models import Provider, ProviderAlert


@pytest.mark.django_db
class TestAnalyticsAPI(APITestCase):
    """Test analytics API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.provider = Provider.objects.create(
            name="Test Provider",
            tax_id="B12345678",
        )

        # Create some contracts
        for i in range(5):
            Contract.objects.create(
                external_id=f"TEST-{i:03d}",
                title=f"Contract {i}",
                contract_type="SERVICES",
                status="AWARDED",
                budget=Decimal("100000"),
                publication_date=timezone.now().date(),
                region="Madrid",
                contracting_authority="Test Authority",
                source_platform="TEST",
                risk_score=Decimal(str(20 + i * 15)),  # 20, 35, 50, 65, 80
            )

        # Create alert
        ProviderAlert.objects.create(
            provider=self.provider,
            severity="CRITICAL",
            alert_type="HIGH_RISK_CONTRACT",
            title="Test Alert",
            description="Test",
            is_resolved=False,
        )

    def test_dashboard_stats(self):
        """Test dashboard statistics endpoint."""
        url = reverse("analytics-dashboard")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_contracts"] == 5
        assert response.data["total_providers"] == 1
        assert response.data["critical_alerts"] == 1
        assert "avg_risk_score" in response.data

    def test_regional_stats(self):
        """Test regional statistics endpoint."""
        url = reverse("analytics-regional-stats")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["region"] == "Madrid"
        assert response.data[0]["total_contracts"] == 5

    def test_trends(self):
        """Test trends endpoint."""
        url = reverse("analytics-trends")
        response = self.client.get(url, {"days": 30})

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        # Should have at least one data point
        assert len(response.data) >= 1

    def test_contract_type_distribution(self):
        """Test contract type distribution endpoint."""
        url = reverse("analytics-contract-type-distribution")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["contract_type"] == "SERVICES"
        assert response.data[0]["count"] == 5

    def test_top_providers(self):
        """Test top providers endpoint."""
        url = reverse("analytics-top-providers")
        response = self.client.get(url, {"limit": 5})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["provider_name"] == "Test Provider"

    def test_risk_distribution(self):
        """Test risk distribution endpoint."""
        url = reverse("analytics-risk-distribution")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "minimal" in response.data
        assert "low" in response.data
        assert "medium" in response.data
        assert "high" in response.data
        assert "critical" in response.data

        # Check counts
        assert response.data["minimal"] == 1  # 20
        assert response.data["low"] == 1      # 35
        assert response.data["medium"] == 1   # 50
        assert response.data["high"] == 1     # 65
        assert response.data["critical"] == 1  # 80

    def test_alerts_summary(self):
        """Test alerts summary endpoint."""
        url = reverse("analytics-alerts-summary")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "by_severity" in response.data
        assert "by_type" in response.data
        assert response.data["total_unresolved"] == 1

    def test_recent_high_risk(self):
        """Test recent high-risk contracts endpoint."""
        url = reverse("analytics-recent-high-risk")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Should return contracts with risk > 70
        assert len(response.data) == 1
        assert response.data[0]["external_id"] == "TEST-004"


@pytest.mark.django_db
class TestAnalyticsWithMultipleRegions(APITestCase):
    """Test analytics with data from multiple regions."""

    def setUp(self):
        """Create data across multiple regions."""
        regions = ["Madrid", "Barcelona", "Valencia"]

        for region in regions:
            for i in range(3):
                Contract.objects.create(
                    external_id=f"{region}-{i}",
                    title=f"Contract {i}",
                    contract_type="SERVICES",
                    status="AWARDED",
                    budget=Decimal("100000"),
                    publication_date=timezone.now().date(),
                    region=region,
                    contracting_authority="Test Authority",
                    source_platform="TEST",
                    risk_score=Decimal("50"),
                )

    def test_regional_distribution(self):
        """Test regional statistics with multiple regions."""
        url = reverse("analytics-regional-stats")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

        regions = [item["region"] for item in response.data]
        assert "Madrid" in regions
        assert "Barcelona" in regions
        assert "Valencia" in regions
