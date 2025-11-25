"""
Overpricing detection model.

Detects contracts that are priced significantly above market rates
by comparing against historical data and regional averages.
"""
from decimal import Decimal

from django.db.models import Avg, Q

from apps.analytics.ai.base import ContractAIModel
from apps.contracts.models import Contract


class OverpricingDetector(ContractAIModel):
    """
    Detect overpriced contracts.

    Compares contract budget/awarded amount against:
    - Regional average for similar contract types
    - Historical average for same contracting authority
    - National average for similar contracts
    """

    name = "overpricing_detector"

    # Thresholds for overpricing
    HIGH_OVERPRICING_THRESHOLD = Decimal("30")  # 30% above average
    MEDIUM_OVERPRICING_THRESHOLD = Decimal("15")  # 15% above average

    def calculate_score(self, contract: Contract) -> Decimal:
        """
        Calculate overpricing risk score.

        Args:
            contract: Contract instance

        Returns:
            Risk score (0-100), where 100 is extremely overpriced
        """
        self.validate_contract(contract)

        # Get the amount to analyze (awarded if available, else budget)
        amount = contract.awarded_amount or contract.budget

        # Calculate different comparison metrics
        regional_avg = self._get_regional_average(contract)
        authority_avg = self._get_authority_average(contract)
        national_avg = self._get_national_average(contract)

        # Calculate deviation percentages
        deviations = []

        if regional_avg and regional_avg > 0:
            regional_dev = ((amount - regional_avg) / regional_avg) * 100
            deviations.append(regional_dev)

        if authority_avg and authority_avg > 0:
            authority_dev = ((amount - authority_avg) / authority_avg) * 100
            deviations.append(authority_dev)

        if national_avg and national_avg > 0:
            national_dev = ((amount - national_avg) / national_avg) * 100
            deviations.append(national_dev)

        if not deviations:
            # Not enough data to compare
            return Decimal("0")

        # Use the maximum deviation (most conservative)
        max_deviation = max(deviations)

        # Convert deviation to risk score
        score = self._deviation_to_score(Decimal(str(max_deviation)))

        return score

    def _get_regional_average(self, contract: Contract) -> Decimal | None:
        """
        Get average contract amount for same region and type.

        Args:
            contract: Contract instance

        Returns:
            Average amount or None
        """
        queryset = Contract.objects.filter(
            region=contract.region,
            contract_type=contract.contract_type,
            status__in=["AWARDED", "COMPLETED"],
        ).exclude(id=contract.id)

        # Use awarded amount if available, else budget
        avg_data = queryset.aggregate(
            avg_awarded=Avg("awarded_amount"),
            avg_budget=Avg("budget"),
        )

        avg_awarded = avg_data.get("avg_awarded")
        avg_budget = avg_data.get("avg_budget")

        return avg_awarded or avg_budget

    def _get_authority_average(self, contract: Contract) -> Decimal | None:
        """
        Get average contract amount for same contracting authority.

        Args:
            contract: Contract instance

        Returns:
            Average amount or None
        """
        queryset = Contract.objects.filter(
            contracting_authority=contract.contracting_authority,
            contract_type=contract.contract_type,
            status__in=["AWARDED", "COMPLETED"],
        ).exclude(id=contract.id)

        avg_data = queryset.aggregate(
            avg_awarded=Avg("awarded_amount"),
            avg_budget=Avg("budget"),
        )

        avg_awarded = avg_data.get("avg_awarded")
        avg_budget = avg_data.get("avg_budget")

        return avg_awarded or avg_budget

    def _get_national_average(self, contract: Contract) -> Decimal | None:
        """
        Get national average for same contract type.

        Args:
            contract: Contract instance

        Returns:
            Average amount or None
        """
        queryset = Contract.objects.filter(
            contract_type=contract.contract_type,
            status__in=["AWARDED", "COMPLETED"],
        ).exclude(id=contract.id)

        avg_data = queryset.aggregate(
            avg_awarded=Avg("awarded_amount"),
            avg_budget=Avg("budget"),
        )

        avg_awarded = avg_data.get("avg_awarded")
        avg_budget = avg_data.get("avg_budget")

        return avg_awarded or avg_budget

    def _deviation_to_score(self, deviation: Decimal) -> Decimal:
        """
        Convert price deviation to risk score.

        Args:
            deviation: Percentage deviation from average

        Returns:
            Risk score (0-100)
        """
        if deviation <= 0:
            # Below or equal to average - no risk
            return Decimal("0")

        if deviation < self.MEDIUM_OVERPRICING_THRESHOLD:
            # Slight overpricing - low risk
            ratio = deviation / self.MEDIUM_OVERPRICING_THRESHOLD
            return ratio * Decimal("40")  # 0-40 score

        elif deviation < self.HIGH_OVERPRICING_THRESHOLD:
            # Medium overpricing - medium risk
            ratio = (deviation - self.MEDIUM_OVERPRICING_THRESHOLD) / (
                self.HIGH_OVERPRICING_THRESHOLD - self.MEDIUM_OVERPRICING_THRESHOLD
            )
            return Decimal("40") + (ratio * Decimal("30"))  # 40-70 score

        else:
            # High overpricing - high risk
            excess = deviation - self.HIGH_OVERPRICING_THRESHOLD
            # Cap at 100
            return min(Decimal("70") + excess, Decimal("100"))

    def _generate_explanation(self, contract: Contract, score: Decimal) -> str:
        """
        Generate explanation for overpricing score.

        Args:
            contract: Contract instance
            score: Calculated score

        Returns:
            Human-readable explanation
        """
        if score == 0:
            return "Contract price is within normal market range"

        amount = contract.awarded_amount or contract.budget
        regional_avg = self._get_regional_average(contract)

        if regional_avg and regional_avg > 0:
            deviation = ((amount - regional_avg) / regional_avg) * 100

            if score < 40:
                return f"Contract is {deviation:.1f}% above regional average (slight overpricing)"
            elif score < 70:
                return f"Contract is {deviation:.1f}% above regional average (moderate overpricing)"
            else:
                return f"Contract is {deviation:.1f}% above regional average (significant overpricing)"

        return "Insufficient data for comparison, but indicators suggest potential overpricing"

    def _get_risk_factors(self, contract: Contract) -> list[dict[str, any]]:
        """
        Get detailed risk factors.

        Args:
            contract: Contract instance

        Returns:
            List of risk factor dictionaries
        """
        factors = []
        amount = contract.awarded_amount or contract.budget

        # Regional comparison
        regional_avg = self._get_regional_average(contract)
        if regional_avg and regional_avg > 0:
            deviation = ((amount - regional_avg) / regional_avg) * 100
            factors.append(
                {
                    "factor": "Regional Comparison",
                    "value": f"{deviation:.1f}% deviation",
                    "reference": f"Regional average: €{regional_avg:,.2f}",
                    "risk_level": "high" if deviation > 30 else "medium" if deviation > 15 else "low",
                }
            )

        # Authority comparison
        authority_avg = self._get_authority_average(contract)
        if authority_avg and authority_avg > 0:
            deviation = ((amount - authority_avg) / authority_avg) * 100
            factors.append(
                {
                    "factor": "Authority History",
                    "value": f"{deviation:.1f}% deviation",
                    "reference": f"Authority average: €{authority_avg:,.2f}",
                    "risk_level": "high" if deviation > 30 else "medium" if deviation > 15 else "low",
                }
            )

        return factors
