"""
Risk calculation service.

Orchestrates all AI models to calculate comprehensive
risk scores for contracts and providers.
"""
import logging
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.analytics.ai.corruption_risk import CorruptionRiskScorer
from apps.analytics.ai.delay_prediction import DelayPredictor
from apps.analytics.ai.overpricing import OverpricingDetector
from apps.analytics.ai.provider_analysis import ProviderAnalyzer
from apps.contracts.models import Contract
from apps.providers.models import Provider

logger = logging.getLogger(__name__)


class RiskCalculator:
    """
    Calculate risk scores for contracts and providers.

    Aggregates results from multiple AI models to produce
    comprehensive risk assessments.
    """

    # Weights for different risk components (must sum to 1.0)
    OVERPRICING_WEIGHT = Decimal("0.35")
    CORRUPTION_WEIGHT = Decimal("0.35")
    DELAY_WEIGHT = Decimal("0.20")
    FINANCIAL_WEIGHT = Decimal("0.10")

    def __init__(self) -> None:
        """Initialize risk calculator with AI models."""
        self.overpricing_detector = OverpricingDetector()
        self.corruption_scorer = CorruptionRiskScorer()
        self.delay_predictor = DelayPredictor()
        self.provider_analyzer = ProviderAnalyzer()

    @transaction.atomic
    def analyze_contract(self, contract: Contract) -> dict[str, Any]:
        """
        Perform comprehensive risk analysis on contract.

        Args:
            contract: Contract instance

        Returns:
            Dictionary with all risk scores and analysis
        """
        logger.info(f"Analyzing contract: {contract.external_id}")

        results = {}

        try:
            # Run individual AI models
            results["overpricing"] = self.overpricing_detector.analyze(contract)
            results["corruption"] = self.corruption_scorer.analyze(contract)
            results["delay"] = self.delay_predictor.analyze(contract)

            # Calculate financial risk (simple for now)
            results["financial"] = self._calculate_financial_risk(contract)

            # Calculate overall risk score
            overall_score = self._calculate_overall_score(results)

            # Update contract with risk scores
            contract.risk_score = overall_score
            contract.corruption_risk = Decimal(str(results["corruption"]["score"]))
            contract.delay_risk = Decimal(str(results["delay"]["score"]))
            contract.financial_risk = Decimal(str(results["financial"]["score"]))

            # Set flags
            contract.is_overpriced = results["overpricing"]["score"] > 40
            contract.analyzed_at = timezone.now()
            contract.analysis_version = "1.0"

            contract.save(
                update_fields=[
                    "risk_score",
                    "corruption_risk",
                    "delay_risk",
                    "financial_risk",
                    "is_overpriced",
                    "analyzed_at",
                    "analysis_version",
                ]
            )

            results["overall"] = {
                "score": float(overall_score),
                "level": self._get_risk_level(overall_score),
                "explanation": self._get_overall_explanation(overall_score),
            }

            logger.info(
                f"Contract {contract.external_id} analyzed: "
                f"Risk score {overall_score:.2f}"
            )

            return results

        except Exception as e:
            logger.error(f"Failed to analyze contract {contract.external_id}: {e}")
            raise

    def analyze_provider(self, provider: Provider) -> dict[str, Any]:
        """
        Analyze provider risk.

        Args:
            provider: Provider instance

        Returns:
            Dictionary with provider risk analysis
        """
        logger.info(f"Analyzing provider: {provider.name}")

        try:
            results = self.provider_analyzer.analyze(provider)

            # Update provider risk score
            provider.risk_score = Decimal(str(results["score"]))

            # Flag if high risk
            if provider.risk_score > 60:
                provider.is_flagged = True
                provider.flag_reason = results["explanation"]

            provider.save(update_fields=["risk_score", "is_flagged", "flag_reason"])

            logger.info(f"Provider {provider.name} analyzed: Risk score {results['score']:.2f}")

            return results

        except Exception as e:
            logger.error(f"Failed to analyze provider {provider.name}: {e}")
            raise

    def _calculate_financial_risk(self, contract: Contract) -> dict[str, Any]:
        """
        Calculate financial risk for contract.

        Args:
            contract: Contract instance

        Returns:
            Financial risk analysis
        """
        score = Decimal("0")
        factors = []

        # Large contracts carry inherent financial risk
        if contract.budget > 10000000:
            score += Decimal("30")
            factors.append(
                {
                    "factor": "Large Budget",
                    "description": f"Budget exceeds €10M",
                    "risk_level": "high",
                }
            )
        elif contract.budget > 5000000:
            score += Decimal("20")
            factors.append(
                {
                    "factor": "Significant Budget",
                    "description": f"Budget exceeds €5M",
                    "risk_level": "medium",
                }
            )

        # Check for budget overruns
        if contract.awarded_amount and contract.budget:
            overrun_pct = (
                (contract.awarded_amount - contract.budget) / contract.budget
            ) * 100

            if overrun_pct > 20:
                score += Decimal("40")
                factors.append(
                    {
                        "factor": "Budget Overrun",
                        "description": f"{overrun_pct:.1f}% over budget",
                        "risk_level": "high",
                    }
                )
            elif overrun_pct > 10:
                score += Decimal("20")
                factors.append(
                    {
                        "factor": "Budget Overrun",
                        "description": f"{overrun_pct:.1f}% over budget",
                        "risk_level": "medium",
                    }
                )

        # Cap at 100
        score = min(score, Decimal("100"))

        return {
            "score": float(score),
            "model": "financial_risk",
            "explanation": self._get_financial_explanation(score),
            "factors": factors,
        }

    def _calculate_overall_score(self, results: dict[str, Any]) -> Decimal:
        """
        Calculate weighted overall risk score.

        Args:
            results: Dictionary of individual model results

        Returns:
            Overall risk score
        """
        overpricing_score = Decimal(str(results["overpricing"]["score"]))
        corruption_score = Decimal(str(results["corruption"]["score"]))
        delay_score = Decimal(str(results["delay"]["score"]))
        financial_score = Decimal(str(results["financial"]["score"]))

        overall = (
            (overpricing_score * self.OVERPRICING_WEIGHT)
            + (corruption_score * self.CORRUPTION_WEIGHT)
            + (delay_score * self.DELAY_WEIGHT)
            + (financial_score * self.FINANCIAL_WEIGHT)
        )

        return overall

    def _get_risk_level(self, score: Decimal) -> str:
        """
        Convert score to risk level.

        Args:
            score: Risk score

        Returns:
            Risk level string
        """
        if score >= 75:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        elif score >= 20:
            return "LOW"
        else:
            return "MINIMAL"

    def _get_overall_explanation(self, score: Decimal) -> str:
        """
        Get explanation for overall risk score.

        Args:
            score: Overall risk score

        Returns:
            Human-readable explanation
        """
        if score >= 75:
            return "Critical risk level - immediate investigation required"
        elif score >= 60:
            return "High risk level - detailed review recommended"
        elif score >= 40:
            return "Medium risk level - monitoring advised"
        elif score >= 20:
            return "Low risk level - standard oversight sufficient"
        else:
            return "Minimal risk level - normal procurement process"

    def _get_financial_explanation(self, score: Decimal) -> str:
        """
        Get explanation for financial risk.

        Args:
            score: Financial risk score

        Returns:
            Explanation string
        """
        if score >= 60:
            return "High financial risk due to budget size and/or overruns"
        elif score >= 30:
            return "Moderate financial risk requiring oversight"
        else:
            return "Low financial risk"
