"""Tests for AI models."""
from decimal import Decimal

import pytest
from django.test import TestCase
from django.utils import timezone

from apps.analytics.ai.corruption_risk import CorruptionRiskScorer
from apps.analytics.ai.delay_prediction import DelayPredictor
from apps.analytics.ai.overpricing import OverpricingDetector
from apps.analytics.ai.provider_analysis import ProviderAnalyzer
from apps.contracts.models import Contract, ContractAmendment
from apps.providers.models import Provider


@pytest.mark.django_db
class TestOverpricingDetector(TestCase):
    """Test overpricing detection model."""

    def setUp(self):
        """Set up test data."""
        self.detector = OverpricingDetector()
        self.provider = Provider.objects.create(
            name="Test Provider", tax_id="B12345678"
        )

    def test_no_overpricing(self):
        """Test contract with normal pricing."""
        # Create baseline contracts
        for i in range(5):
            Contract.objects.create(
                external_id=f"TEST-{i}",
                title="Test Contract",
                contract_type="SERVICES",
                status="AWARDED",
                budget=Decimal("100000"),
                awarded_amount=Decimal("100000"),
                region="Madrid",
                contracting_authority="Test Authority",
                source_platform="TEST",
            )

        # Create test contract with similar price
        contract = Contract.objects.create(
            external_id="TEST-NEW",
            title="New Contract",
            contract_type="SERVICES",
            status="PUBLISHED",
            budget=Decimal("105000"),  # 5% above average
            region="Madrid",
            contracting_authority="Test Authority",
            source_platform="TEST",
        )

        score = self.detector.calculate_score(contract)
        assert score < 40  # Should be low risk

    def test_significant_overpricing(self):
        """Test contract with significant overpricing."""
        # Create baseline contracts
        for i in range(5):
            Contract.objects.create(
                external_id=f"TEST-{i}",
                title="Test Contract",
                contract_type="SERVICES",
                status="AWARDED",
                budget=Decimal("100000"),
                awarded_amount=Decimal("100000"),
                region="Madrid",
                contracting_authority="Test Authority",
                source_platform="TEST",
            )

        # Create overpriced contract (50% more expensive)
        contract = Contract.objects.create(
            external_id="TEST-OVERPRICED",
            title="Overpriced Contract",
            contract_type="SERVICES",
            status="PUBLISHED",
            budget=Decimal("150000"),  # 50% above average
            region="Madrid",
            contracting_authority="Test Authority",
            source_platform="TEST",
        )

        score = self.detector.calculate_score(contract)
        assert score > 70  # Should be high risk

    def test_no_comparison_data(self):
        """Test contract with no historical data for comparison."""
        contract = Contract.objects.create(
            external_id="TEST-ALONE",
            title="Unique Contract",
            contract_type="SUPPLIES",  # No other contracts of this type
            status="PUBLISHED",
            budget=Decimal("100000"),
            region="Barcelona",
            contracting_authority="New Authority",
            source_platform="TEST",
        )

        score = self.detector.calculate_score(contract)
        assert score == 0  # No data to compare


@pytest.mark.django_db
class TestCorruptionRiskScorer(TestCase):
    """Test corruption risk scoring model."""

    def setUp(self):
        """Set up test data."""
        self.scorer = CorruptionRiskScorer()
        self.provider = Provider.objects.create(
            name="Test Provider", tax_id="B12345678"
        )

    def test_normal_contract(self):
        """Test contract with normal characteristics."""
        contract = Contract.objects.create(
            external_id="TEST-NORMAL",
            title="Normal Contract",
            contract_type="SERVICES",
            status="PUBLISHED",
            budget=Decimal("100000"),
            procedure_type="OPEN",
            publication_date=timezone.now().date(),
            deadline_date=timezone.now().date() + timezone.timedelta(days=45),
            region="Madrid",
            contracting_authority="Test Authority",
            source_platform="TEST",
            awarded_to=self.provider,
        )

        score = self.scorer.calculate_score(contract)
        assert score < 40  # Should be low risk

    def test_rushed_tender(self):
        """Test contract with suspiciously short deadline."""
        contract = Contract.objects.create(
            external_id="TEST-RUSHED",
            title="Rushed Contract",
            contract_type="SERVICES",
            status="PUBLISHED",
            budget=Decimal("100000"),
            procedure_type="OPEN",
            publication_date=timezone.now().date(),
            deadline_date=timezone.now().date() + timezone.timedelta(days=5),  # Only 5 days
            region="Madrid",
            contracting_authority="Test Authority",
            source_platform="TEST",
            awarded_to=self.provider,
        )

        score = self.scorer.calculate_score(contract)
        assert score > 20  # Should have some risk

    def test_provider_dominance(self):
        """Test detection of provider dominance."""
        # Create multiple contracts awarded to same provider by same authority
        for i in range(10):
            Contract.objects.create(
                external_id=f"TEST-{i}",
                title=f"Contract {i}",
                contract_type="SERVICES",
                status="AWARDED",
                budget=Decimal("100000"),
                contracting_authority="Test Authority",
                source_platform="TEST",
                awarded_to=self.provider,
            )

        # Create test contract
        contract = Contract.objects.create(
            external_id="TEST-NEW",
            title="New Contract",
            contract_type="SERVICES",
            status="PUBLISHED",
            budget=Decimal("100000"),
            contracting_authority="Test Authority",
            source_platform="TEST",
            awarded_to=self.provider,
        )

        score = self.scorer.calculate_score(contract)
        assert score > 20  # Should detect dominance

    def test_threshold_gaming(self):
        """Test detection of threshold gaming."""
        contract = Contract.objects.create(
            external_id="TEST-THRESHOLD",
            title="Near Threshold Contract",
            contract_type="MINOR",
            status="PUBLISHED",
            budget=Decimal("39500"),  # Just below 40k threshold
            procedure_type="MINOR",
            region="Madrid",
            contracting_authority="Test Authority",
            source_platform="TEST",
        )

        score = self.scorer.calculate_score(contract)
        assert score > 0  # Should detect threshold gaming


@pytest.mark.django_db
class TestDelayPredictor(TestCase):
    """Test delay prediction model."""

    def setUp(self):
        """Set up test data."""
        self.predictor = DelayPredictor()
        self.provider = Provider.objects.create(
            name="Test Provider", tax_id="B12345678"
        )

    def test_reliable_provider(self):
        """Test provider with good track record."""
        # Create completed contracts with no delays
        for i in range(10):
            Contract.objects.create(
                external_id=f"TEST-{i}",
                title=f"Contract {i}",
                contract_type="SERVICES",
                status="COMPLETED",
                budget=Decimal("100000"),
                awarded_to=self.provider,
                has_delays=False,
                contracting_authority="Test Authority",
                source_platform="TEST",
            )

        # Test new contract
        contract = Contract.objects.create(
            external_id="TEST-NEW",
            title="New Contract",
            contract_type="SERVICES",
            status="AWARDED",
            budget=Decimal("100000"),
            awarded_to=self.provider,
            contracting_authority="Test Authority",
            source_platform="TEST",
        )

        score = self.predictor.calculate_score(contract)
        assert score < 30  # Should be low risk

    def test_unreliable_provider(self):
        """Test provider with poor track record."""
        # Create completed contracts with frequent delays
        for i in range(10):
            Contract.objects.create(
                external_id=f"TEST-{i}",
                title=f"Contract {i}",
                contract_type="SERVICES",
                status="COMPLETED",
                budget=Decimal("100000"),
                awarded_to=self.provider,
                has_delays=True,  # All delayed
                contracting_authority="Test Authority",
                source_platform="TEST",
            )

        # Test new contract
        contract = Contract.objects.create(
            external_id="TEST-NEW",
            title="New Contract",
            contract_type="SERVICES",
            status="AWARDED",
            budget=Decimal("100000"),
            awarded_to=self.provider,
            contracting_authority="Test Authority",
            source_platform="TEST",
        )

        score = self.predictor.calculate_score(contract)
        assert score > 30  # Should be high risk

    def test_complex_contract(self):
        """Test large complex contract has higher risk."""
        contract_small = Contract.objects.create(
            external_id="TEST-SMALL",
            title="Small Contract",
            contract_type="SERVICES",
            status="AWARDED",
            budget=Decimal("50000"),
            awarded_to=self.provider,
            contracting_authority="Test Authority",
            source_platform="TEST",
        )

        contract_large = Contract.objects.create(
            external_id="TEST-LARGE",
            title="Large Contract",
            contract_type="WORKS",
            status="AWARDED",
            budget=Decimal("15000000"),
            awarded_to=self.provider,
            contracting_authority="Test Authority",
            source_platform="TEST",
        )

        score_small = self.predictor.calculate_score(contract_small)
        score_large = self.predictor.calculate_score(contract_large)

        assert score_large > score_small  # Large should be higher risk


@pytest.mark.django_db
class TestProviderAnalyzer(TestCase):
    """Test provider analysis model."""

    def setUp(self):
        """Set up test data."""
        self.analyzer = ProviderAnalyzer()

    def test_established_provider(self):
        """Test established provider with normal patterns."""
        provider = Provider.objects.create(
            name="Established Corp",
            tax_id="B12345678",
            total_contracts=50,
            total_awarded_amount=Decimal("5000000"),
            success_rate=Decimal("45"),  # Normal win rate
            first_contract_date=timezone.now().date() - timezone.timedelta(days=1825),  # 5 years ago
        )

        score = self.analyzer.calculate_score(provider)
        assert score < 30  # Should be low risk

    def test_new_provider_large_contracts(self):
        """Test new provider with suspiciously large contracts."""
        provider = Provider.objects.create(
            name="New Corp",
            tax_id="B87654321",
            total_contracts=2,
            total_awarded_amount=Decimal("2000000"),  # Large for new provider
            success_rate=Decimal("90"),  # Very high win rate
            first_contract_date=timezone.now().date() - timezone.timedelta(days=180),  # 6 months ago
        )

        score = self.analyzer.calculate_score(provider)
        assert score > 30  # Should be high risk

    def test_high_win_rate(self):
        """Test provider with suspiciously high win rate."""
        provider = Provider.objects.create(
            name="Lucky Corp",
            tax_id="B11111111",
            total_contracts=20,
            total_awarded_amount=Decimal("1000000"),
            success_rate=Decimal("85"),  # Very high win rate
            first_contract_date=timezone.now().date() - timezone.timedelta(days=730),  # 2 years ago
        )

        score = self.analyzer.calculate_score(provider)
        assert score > 0  # Should detect high win rate


@pytest.mark.django_db
class TestAIModelIntegration(TestCase):
    """Integration tests for AI models."""

    def test_all_models_return_valid_scores(self):
        """Test all models return scores in valid range."""
        provider = Provider.objects.create(
            name="Test Provider",
            tax_id="B12345678",
            total_contracts=10,
            total_awarded_amount=Decimal("1000000"),
            first_contract_date=timezone.now().date() - timezone.timedelta(days=365),
        )

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
            awarded_to=provider,
        )

        # Test all models
        overpricing = OverpricingDetector()
        corruption = CorruptionRiskScorer()
        delay = DelayPredictor()
        provider_analyzer = ProviderAnalyzer()

        # All should return valid scores
        assert 0 <= overpricing.calculate_score(contract) <= 100
        assert 0 <= corruption.calculate_score(contract) <= 100
        assert 0 <= delay.calculate_score(contract) <= 100
        assert 0 <= provider_analyzer.calculate_score(provider) <= 100
