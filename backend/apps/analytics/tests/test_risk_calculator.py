"""Tests for risk calculator service."""
from decimal import Decimal

import pytest
from django.test import TestCase
from django.utils import timezone

from apps.analytics.services.alert_generator import AlertGenerator
from apps.analytics.services.risk_calculator import RiskCalculator
from apps.contracts.models import Contract
from apps.providers.models import Provider, ProviderAlert


@pytest.mark.django_db
class TestRiskCalculator(TestCase):
    """Test RiskCalculator service."""

    def setUp(self):
        """Set up test data."""
        self.calculator = RiskCalculator()
        self.provider = Provider.objects.create(
            name="Test Provider",
            tax_id="B12345678",
            total_contracts=10,
            total_awarded_amount=Decimal("1000000"),
            first_contract_date=timezone.now().date() - timezone.timedelta(days=365),
        )

    def test_analyze_contract(self):
        """Test contract analysis."""
        contract = Contract.objects.create(
            external_id="TEST-001",
            title="Test Contract",
            contract_type="SERVICES",
            status="AWARDED",
            budget=Decimal("100000"),
            awarded_amount=Decimal("105000"),
            procedure_type="OPEN",
            publication_date=timezone.now().date() - timezone.timedelta(days=60),
            deadline_date=timezone.now().date() - timezone.timedelta(days=30),
            award_date=timezone.now().date(),
            region="Madrid",
            contracting_authority="Test Authority",
            source_platform="TEST",
            awarded_to=self.provider,
        )

        result = self.calculator.analyze_contract(contract)

        # Check result structure
        assert "overpricing" in result
        assert "corruption" in result
        assert "delay" in result
        assert "financial" in result
        assert "overall" in result

        # Check scores are valid
        assert 0 <= result["overpricing"]["score"] <= 100
        assert 0 <= result["corruption"]["score"] <= 100
        assert 0 <= result["delay"]["score"] <= 100
        assert 0 <= result["financial"]["score"] <= 100
        assert 0 <= result["overall"]["score"] <= 100

        # Check contract was updated
        contract.refresh_from_db()
        assert contract.risk_score is not None
        assert contract.analyzed_at is not None

    def test_analyze_provider(self):
        """Test provider analysis."""
        result = self.calculator.analyze_provider(self.provider)

        # Check result structure
        assert "score" in result
        assert "explanation" in result

        # Check score is valid
        assert 0 <= result["score"] <= 100

        # Check provider was updated
        self.provider.refresh_from_db()
        assert self.provider.risk_score is not None

    def test_risk_level_classification(self):
        """Test risk level classification."""
        # Test different score levels
        assert self.calculator._get_risk_level(Decimal("10")) == "MINIMAL"
        assert self.calculator._get_risk_level(Decimal("30")) == "LOW"
        assert self.calculator._get_risk_level(Decimal("50")) == "MEDIUM"
        assert self.calculator._get_risk_level(Decimal("70")) == "HIGH"
        assert self.calculator._get_risk_level(Decimal("90")) == "CRITICAL"

    def test_financial_risk_calculation(self):
        """Test financial risk calculation."""
        # Small contract
        contract_small = Contract.objects.create(
            external_id="TEST-SMALL",
            title="Small Contract",
            contract_type="SERVICES",
            status="AWARDED",
            budget=Decimal("50000"),
            awarded_amount=Decimal("50000"),
            region="Madrid",
            contracting_authority="Test Authority",
            source_platform="TEST",
        )

        # Large contract
        contract_large = Contract.objects.create(
            external_id="TEST-LARGE",
            title="Large Contract",
            contract_type="SERVICES",
            status="AWARDED",
            budget=Decimal("15000000"),
            awarded_amount=Decimal("15000000"),
            region="Madrid",
            contracting_authority="Test Authority",
            source_platform="TEST",
        )

        result_small = self.calculator._calculate_financial_risk(contract_small)
        result_large = self.calculator._calculate_financial_risk(contract_large)

        # Large contract should have higher financial risk
        assert result_large["score"] > result_small["score"]

    def test_overall_score_weighting(self):
        """Test that overall score is properly weighted."""
        results = {
            "overpricing": {"score": 50},
            "corruption": {"score": 50},
            "delay": {"score": 50},
            "financial": {"score": 50},
        }

        overall = self.calculator._calculate_overall_score(results)

        # Should be weighted average
        expected = (
            (Decimal("50") * self.calculator.OVERPRICING_WEIGHT)
            + (Decimal("50") * self.calculator.CORRUPTION_WEIGHT)
            + (Decimal("50") * self.calculator.DELAY_WEIGHT)
            + (Decimal("50") * self.calculator.FINANCIAL_WEIGHT)
        )

        assert overall == expected


@pytest.mark.django_db
class TestAlertGenerator(TestCase):
    """Test AlertGenerator service."""

    def setUp(self):
        """Set up test data."""
        self.generator = AlertGenerator()
        self.provider = Provider.objects.create(
            name="Test Provider",
            tax_id="B12345678",
        )

    def test_generate_high_risk_alert(self):
        """Test alert generation for high-risk contract."""
        contract = Contract.objects.create(
            external_id="TEST-HIGH-RISK",
            title="High Risk Contract",
            contract_type="SERVICES",
            status="AWARDED",
            budget=Decimal("100000"),
            region="Madrid",
            contracting_authority="Test Authority",
            source_platform="TEST",
            awarded_to=self.provider,
        )

        analysis = {
            "overall": {"score": 75.0, "level": "HIGH", "explanation": "High risk"},
            "overpricing": {"score": 80.0, "explanation": "Overpriced"},
            "corruption": {"score": 70.0, "explanation": "Corruption indicators"},
            "delay": {"score": 50.0},
        }

        alerts = self.generator.generate_contract_alerts(contract, analysis)

        # Should generate alerts
        assert len(alerts) > 0
        assert all(isinstance(alert, ProviderAlert) for alert in alerts)

    def test_no_alert_for_low_risk(self):
        """Test no alerts generated for low-risk contract."""
        contract = Contract.objects.create(
            external_id="TEST-LOW-RISK",
            title="Low Risk Contract",
            contract_type="SERVICES",
            status="AWARDED",
            budget=Decimal("100000"),
            region="Madrid",
            contracting_authority="Test Authority",
            source_platform="TEST",
            awarded_to=self.provider,
        )

        analysis = {
            "overall": {"score": 25.0, "level": "LOW", "explanation": "Low risk"},
            "overpricing": {"score": 20.0, "explanation": "Normal price"},
            "corruption": {"score": 15.0, "explanation": "Normal patterns"},
            "delay": {"score": 10.0},
        }

        alerts = self.generator.generate_contract_alerts(contract, analysis)

        # Should not generate alerts
        assert len(alerts) == 0

    def test_duplicate_alert_prevention(self):
        """Test that duplicate alerts are not created."""
        contract = Contract.objects.create(
            external_id="TEST-DUP",
            title="Test Contract",
            contract_type="SERVICES",
            status="AWARDED",
            budget=Decimal("100000"),
            region="Madrid",
            contracting_authority="Test Authority",
            source_platform="TEST",
            awarded_to=self.provider,
        )

        analysis = {
            "overall": {"score": 75.0, "level": "HIGH", "explanation": "High risk"},
            "overpricing": {"score": 80.0, "explanation": "Overpriced"},
            "corruption": {"score": 70.0, "explanation": "Corruption indicators"},
            "delay": {"score": 50.0},
        }

        # Generate alerts first time
        alerts1 = self.generator.generate_contract_alerts(contract, analysis)

        # Try to generate again
        alerts2 = self.generator.generate_contract_alerts(contract, analysis)

        # Should not create duplicates
        assert len(alerts1) > 0
        assert len(alerts2) == 0  # Duplicates prevented

    def test_alert_severity_assignment(self):
        """Test correct severity assignment."""
        # Test different score levels
        assert self.generator._get_severity(30.0) == "LOW"
        assert self.generator._get_severity(50.0) == "MEDIUM"
        assert self.generator._get_severity(65.0) == "HIGH"
        assert self.generator._get_severity(80.0) == "CRITICAL"

    def test_provider_alert_generation(self):
        """Test provider alert generation."""
        analysis = {
            "score": 75.0,
            "explanation": "High-risk provider",
            "factors": [],
        }

        alerts = self.generator.generate_provider_alerts(self.provider, analysis)

        # Should generate alert
        assert len(alerts) == 1
        assert alerts[0].provider == self.provider
        assert alerts[0].severity in ["HIGH", "CRITICAL"]
