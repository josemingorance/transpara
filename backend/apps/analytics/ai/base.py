"""
Base AI model for risk analysis.

Provides foundation for all AI models with consistent
interface and scoring methodology.
"""
import logging
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any


class AIModelException(Exception):
    """Base exception for AI model errors."""

    pass


class BaseAIModel(ABC):
    """
    Abstract base class for AI models.

    All AI models must inherit from this class and implement
    the required methods. Provides common functionality for
    scoring, validation, and result formatting.
    """

    # Override in subclasses
    name: str = "base_model"
    min_score: Decimal = Decimal("0")
    max_score: Decimal = Decimal("100")

    def __init__(self) -> None:
        """Initialize AI model."""
        self.logger = logging.getLogger(f"ai.{self.name}")

    @abstractmethod
    def calculate_score(self, data: Any) -> Decimal:
        """
        Calculate risk score.

        Args:
            data: Input data (Contract, Provider, etc.)

        Returns:
            Risk score between min_score and max_score

        Raises:
            AIModelException: If calculation fails
        """
        pass

    def analyze(self, data: Any) -> dict[str, Any]:
        """
        Perform complete analysis.

        Args:
            data: Input data

        Returns:
            Dictionary with score and explanation
        """
        try:
            score = self.calculate_score(data)
            score = self._clamp_score(score)

            return {
                "score": float(score),
                "model": self.name,
                "explanation": self._generate_explanation(data, score),
                "factors": self._get_risk_factors(data),
            }

        except Exception as e:
            self.logger.error(f"Analysis failed: {e}", exc_info=True)
            raise AIModelException(f"Failed to analyze with {self.name}: {e}")

    def _clamp_score(self, score: Decimal) -> Decimal:
        """
        Clamp score to valid range.

        Args:
            score: Raw score

        Returns:
            Clamped score between min_score and max_score
        """
        if score < self.min_score:
            return self.min_score
        if score > self.max_score:
            return self.max_score
        return score

    def _generate_explanation(self, data: Any, score: Decimal) -> str:
        """
        Generate human-readable explanation.

        Args:
            data: Input data
            score: Calculated score

        Returns:
            Explanation string
        """
        # Override in subclasses for specific explanations
        if score > 70:
            return "High risk detected"
        elif score > 40:
            return "Medium risk detected"
        else:
            return "Low risk detected"

    def _get_risk_factors(self, data: Any) -> list[dict[str, Any]]:
        """
        Get list of risk factors.

        Args:
            data: Input data

        Returns:
            List of risk factor dictionaries
        """
        # Override in subclasses for specific factors
        return []


class ContractAIModel(BaseAIModel):
    """Base class for contract-focused AI models."""

    def validate_contract(self, contract: Any) -> None:
        """
        Validate contract has required data.

        Args:
            contract: Contract instance

        Raises:
            AIModelException: If contract is invalid
        """
        if not contract:
            raise AIModelException("Contract is required")

        if not hasattr(contract, "budget") or not contract.budget:
            raise AIModelException("Contract must have a budget")


class ProviderAIModel(BaseAIModel):
    """Base class for provider-focused AI models."""

    def validate_provider(self, provider: Any) -> None:
        """
        Validate provider has required data.

        Args:
            provider: Provider instance

        Raises:
            AIModelException: If provider is invalid
        """
        if not provider:
            raise AIModelException("Provider is required")

        if not hasattr(provider, "tax_id") or not provider.tax_id:
            raise AIModelException("Provider must have a tax_id")
