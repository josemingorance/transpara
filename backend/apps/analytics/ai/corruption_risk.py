"""
Corruption risk scoring model.

Analyzes contracts for patterns that may indicate corruption
or irregular procurement practices.
"""
from decimal import Decimal

from django.db.models import Count

from apps.analytics.ai.base import ContractAIModel
from apps.contracts.models import Contract


class CorruptionRiskScorer(ContractAIModel):
    """
    Score contracts for corruption risk.

    Analyzes multiple risk factors:
    - Sole provider dominance in region
    - Rushed tender process (short deadlines)
    - Contract amendments frequency
    - Negotiated procedures usage
    - Minor contracts just below threshold
    """

    name = "corruption_risk_scorer"

    def calculate_score(self, contract: Contract) -> Decimal:
        """
        Calculate corruption risk score.

        Args:
            contract: Contract instance

        Returns:
            Risk score (0-100)
        """
        self.validate_contract(contract)

        risk_score = Decimal("0")

        # Factor 1: Provider dominance (0-25 points)
        risk_score += self._analyze_provider_dominance(contract)

        # Factor 2: Tender timeline (0-25 points)
        risk_score += self._analyze_tender_timeline(contract)

        # Factor 3: Amendment frequency (0-20 points)
        risk_score += self._analyze_amendments(contract)

        # Factor 4: Procedure type (0-20 points)
        risk_score += self._analyze_procedure_type(contract)

        # Factor 5: Threshold gaming (0-10 points)
        risk_score += self._analyze_threshold_gaming(contract)

        return risk_score

    def _analyze_provider_dominance(self, contract: Contract) -> Decimal:
        """
        Check if provider dominates contracts in this region/authority.

        Args:
            contract: Contract instance

        Returns:
            Risk score (0-25)
        """
        if not contract.awarded_to:
            return Decimal("0")

        # Count contracts awarded to this provider by same authority
        authority_contracts = Contract.objects.filter(
            contracting_authority=contract.contracting_authority,
            awarded_to=contract.awarded_to,
            status__in=["AWARDED", "COMPLETED"],
        ).count()

        # Count total contracts by this authority
        total_contracts = Contract.objects.filter(
            contracting_authority=contract.contracting_authority,
            status__in=["AWARDED", "COMPLETED"],
        ).count()

        if total_contracts == 0:
            return Decimal("0")

        # Calculate dominance percentage
        dominance = (authority_contracts / total_contracts) * 100

        # Score based on dominance
        if dominance > 50:
            return Decimal("25")  # Very high concentration
        elif dominance > 30:
            return Decimal("18")  # High concentration
        elif dominance > 15:
            return Decimal("10")  # Moderate concentration
        else:
            return Decimal("0")  # Normal

    def _analyze_tender_timeline(self, contract: Contract) -> Decimal:
        """
        Analyze if tender had suspiciously short deadline.

        Args:
            contract: Contract instance

        Returns:
            Risk score (0-25)
        """
        if not contract.publication_date or not contract.deadline_date:
            return Decimal("0")

        # Calculate days between publication and deadline
        days = (contract.deadline_date - contract.publication_date).days

        # Score based on days (shorter = higher risk)
        if days < 7:
            return Decimal("25")  # Extremely rushed
        elif days < 15:
            return Decimal("18")  # Very rushed
        elif days < 30:
            return Decimal("10")  # Somewhat rushed
        else:
            return Decimal("0")  # Normal

    def _analyze_amendments(self, contract: Contract) -> Decimal:
        """
        Check frequency and magnitude of amendments.

        Args:
            contract: Contract instance

        Returns:
            Risk score (0-20)
        """
        if not contract.has_amendments:
            return Decimal("0")

        amendment_count = contract.amendments.count()

        # Check if awarded amount increased significantly from budget
        if contract.awarded_amount and contract.budget:
            increase_pct = (
                (contract.awarded_amount - contract.budget) / contract.budget
            ) * 100

            if increase_pct > 20 and amendment_count > 0:
                return Decimal("20")  # Large increase + amendments
            elif increase_pct > 10 and amendment_count > 0:
                return Decimal("15")  # Moderate increase + amendments
            elif amendment_count > 2:
                return Decimal("10")  # Multiple amendments
            elif amendment_count > 0:
                return Decimal("5")  # Some amendments

        return Decimal("0")

    def _analyze_procedure_type(self, contract: Contract) -> Decimal:
        """
        Analyze if procedure type is appropriate.

        Args:
            contract: Contract instance

        Returns:
            Risk score (0-20)
        """
        # Negotiated procedures can be legitimate but carry more risk
        if contract.procedure_type == "NEGOTIATED":
            # Higher risk for large contracts
            if contract.budget > 500000:
                return Decimal("20")  # Large negotiated contract
            else:
                return Decimal("10")  # Small negotiated contract

        # Minor contracts (under threshold) - less oversight
        elif contract.procedure_type == "MINOR":
            if contract.budget > 40000:  # Close to minor contract limit
                return Decimal("15")
            else:
                return Decimal("5")

        return Decimal("0")

    def _analyze_threshold_gaming(self, contract: Contract) -> Decimal:
        """
        Detect if contract is just below procurement thresholds.

        Args:
            contract: Contract instance

        Returns:
            Risk score (0-10)
        """
        budget = contract.budget

        # EU thresholds (approximate)
        minor_threshold = Decimal("40000")
        medium_threshold = Decimal("140000")
        eu_threshold = Decimal("5350000")

        # Check if suspiciously close to thresholds
        for threshold in [minor_threshold, medium_threshold, eu_threshold]:
            # Within 5% of threshold
            margin = threshold * Decimal("0.05")
            if threshold - margin <= budget < threshold:
                return Decimal("10")  # Suspicious threshold gaming

        return Decimal("0")

    def _generate_explanation(self, contract: Contract, score: Decimal) -> str:
        """
        Generate explanation for corruption risk score.

        Args:
            contract: Contract instance
            score: Calculated score

        Returns:
            Human-readable explanation
        """
        if score < 20:
            return "Contract shows normal procurement patterns"
        elif score < 40:
            return "Contract shows some irregular patterns that warrant review"
        elif score < 60:
            return "Contract shows multiple red flags requiring investigation"
        else:
            return "Contract shows serious corruption risk indicators requiring immediate review"

    def _get_risk_factors(self, contract: Contract) -> list[dict[str, any]]:
        """
        Get detailed corruption risk factors.

        Args:
            contract: Contract instance

        Returns:
            List of risk factor dictionaries
        """
        factors = []

        # Provider dominance
        dominance_score = self._analyze_provider_dominance(contract)
        if dominance_score > 0:
            factors.append(
                {
                    "factor": "Provider Dominance",
                    "score": float(dominance_score),
                    "description": "Provider has won multiple contracts from same authority",
                    "risk_level": "high" if dominance_score > 15 else "medium",
                }
            )

        # Timeline
        timeline_score = self._analyze_tender_timeline(contract)
        if timeline_score > 0:
            days = (
                (contract.deadline_date - contract.publication_date).days
                if contract.deadline_date and contract.publication_date
                else None
            )
            factors.append(
                {
                    "factor": "Rushed Timeline",
                    "score": float(timeline_score),
                    "description": f"Only {days} days between publication and deadline",
                    "risk_level": "high" if timeline_score > 15 else "medium",
                }
            )

        # Amendments
        amendment_score = self._analyze_amendments(contract)
        if amendment_score > 0:
            factors.append(
                {
                    "factor": "Contract Amendments",
                    "score": float(amendment_score),
                    "description": f"Contract has {contract.amendments.count()} amendments",
                    "risk_level": "high" if amendment_score > 10 else "medium",
                }
            )

        # Procedure type
        procedure_score = self._analyze_procedure_type(contract)
        if procedure_score > 0:
            factors.append(
                {
                    "factor": "Procedure Type",
                    "score": float(procedure_score),
                    "description": f"{contract.get_procedure_type_display()} procedure used",
                    "risk_level": "high" if procedure_score > 15 else "medium",
                }
            )

        # Threshold gaming
        threshold_score = self._analyze_threshold_gaming(contract)
        if threshold_score > 0:
            factors.append(
                {
                    "factor": "Threshold Gaming",
                    "score": float(threshold_score),
                    "description": "Contract amount is suspiciously close to procurement threshold",
                    "risk_level": "medium",
                }
            )

        return factors
