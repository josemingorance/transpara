"""
Delay prediction model.

Predicts the likelihood of contract delays based on
historical data and risk factors.
"""
from decimal import Decimal

from django.db.models import Avg, Count, Q

from apps.analytics.ai.base import ContractAIModel
from apps.contracts.models import Contract


class DelayPredictor(ContractAIModel):
    """
    Predict contract delay risk.

    Analyzes:
    - Provider's historical delay rate
    - Contract complexity (budget size)
    - Contract type historical delays
    - Authority's project management track record
    """

    name = "delay_predictor"

    def calculate_score(self, contract: Contract) -> Decimal:
        """
        Calculate delay risk score.

        Args:
            contract: Contract instance

        Returns:
            Risk score (0-100)
        """
        self.validate_contract(contract)

        risk_score = Decimal("0")

        # Factor 1: Provider history (0-35 points)
        risk_score += self._analyze_provider_history(contract)

        # Factor 2: Contract complexity (0-25 points)
        risk_score += self._analyze_complexity(contract)

        # Factor 3: Contract type patterns (0-20 points)
        risk_score += self._analyze_contract_type_history(contract)

        # Factor 4: Authority track record (0-20 points)
        risk_score += self._analyze_authority_history(contract)

        return risk_score

    def _analyze_provider_history(self, contract: Contract) -> Decimal:
        """
        Analyze provider's historical delay rate.

        Args:
            contract: Contract instance

        Returns:
            Risk score (0-35)
        """
        if not contract.awarded_to:
            # Unknown provider = moderate risk
            return Decimal("15")

        # Get provider's past contracts
        past_contracts = Contract.objects.filter(
            awarded_to=contract.awarded_to,
            status="COMPLETED",
            has_delays=True,
        ).count()

        total_contracts = Contract.objects.filter(
            awarded_to=contract.awarded_to,
            status="COMPLETED",
        ).count()

        if total_contracts == 0:
            # No history = higher risk
            return Decimal("25")

        delay_rate = (past_contracts / total_contracts) * 100

        # Score based on delay rate
        if delay_rate > 50:
            return Decimal("35")  # Chronic delays
        elif delay_rate > 30:
            return Decimal("25")  # Frequent delays
        elif delay_rate > 15:
            return Decimal("15")  # Some delays
        else:
            return Decimal("5")  # Good track record

    def _analyze_complexity(self, contract: Contract) -> Decimal:
        """
        Analyze contract complexity based on budget and type.

        Args:
            contract: Contract instance

        Returns:
            Risk score (0-25)
        """
        budget = contract.budget

        # Larger contracts tend to have more delays
        if budget > 10000000:
            complexity_score = Decimal("25")  # Very complex
        elif budget > 5000000:
            complexity_score = Decimal("20")  # Complex
        elif budget > 1000000:
            complexity_score = Decimal("15")  # Moderate
        elif budget > 100000:
            complexity_score = Decimal("10")  # Simple
        else:
            complexity_score = Decimal("5")  # Very simple

        # Works contracts have higher delay risk
        if contract.contract_type == "WORKS":
            complexity_score += Decimal("5")

        return min(complexity_score, Decimal("25"))

    def _analyze_contract_type_history(self, contract: Contract) -> Decimal:
        """
        Analyze historical delay rate for this contract type.

        Args:
            contract: Contract instance

        Returns:
            Risk score (0-20)
        """
        # Get completed contracts of same type
        delayed = Contract.objects.filter(
            contract_type=contract.contract_type,
            status="COMPLETED",
            has_delays=True,
        ).count()

        total = Contract.objects.filter(
            contract_type=contract.contract_type,
            status="COMPLETED",
        ).count()

        if total == 0:
            return Decimal("10")  # No data

        delay_rate = (delayed / total) * 100

        if delay_rate > 40:
            return Decimal("20")  # This type often delayed
        elif delay_rate > 25:
            return Decimal("15")
        elif delay_rate > 15:
            return Decimal("10")
        else:
            return Decimal("5")

    def _analyze_authority_history(self, contract: Contract) -> Decimal:
        """
        Analyze contracting authority's project management record.

        Args:
            contract: Contract instance

        Returns:
            Risk score (0-20)
        """
        # Get authority's past contracts
        delayed = Contract.objects.filter(
            contracting_authority=contract.contracting_authority,
            status="COMPLETED",
            has_delays=True,
        ).count()

        total = Contract.objects.filter(
            contracting_authority=contract.contracting_authority,
            status="COMPLETED",
        ).count()

        if total == 0:
            return Decimal("10")  # No history

        delay_rate = (delayed / total) * 100

        if delay_rate > 40:
            return Decimal("20")  # Poor management
        elif delay_rate > 25:
            return Decimal("15")
        elif delay_rate > 15:
            return Decimal("10")
        else:
            return Decimal("5")  # Good management

    def _generate_explanation(self, contract: Contract, score: Decimal) -> str:
        """
        Generate explanation for delay prediction.

        Args:
            contract: Contract instance
            score: Calculated score

        Returns:
            Human-readable explanation
        """
        if score < 25:
            return "Low delay risk - contract likely to complete on time"
        elif score < 50:
            return "Moderate delay risk - monitor progress closely"
        elif score < 75:
            return "High delay risk - significant delays are likely"
        else:
            return "Critical delay risk - delays almost certain without intervention"

    def _get_risk_factors(self, contract: Contract) -> list[dict[str, any]]:
        """
        Get detailed delay risk factors.

        Args:
            contract: Contract instance

        Returns:
            List of risk factor dictionaries
        """
        factors = []

        # Provider history
        provider_score = self._analyze_provider_history(contract)
        if contract.awarded_to:
            delayed = Contract.objects.filter(
                awarded_to=contract.awarded_to,
                status="COMPLETED",
                has_delays=True,
            ).count()
            total = Contract.objects.filter(
                awarded_to=contract.awarded_to,
                status="COMPLETED",
            ).count()

            if total > 0:
                delay_rate = (delayed / total) * 100
                factors.append(
                    {
                        "factor": "Provider History",
                        "score": float(provider_score),
                        "description": f"Provider has {delay_rate:.1f}% delay rate ({delayed}/{total} contracts)",
                        "risk_level": "high" if delay_rate > 30 else "medium" if delay_rate > 15 else "low",
                    }
                )

        # Complexity
        complexity_score = self._analyze_complexity(contract)
        if complexity_score > 10:
            factors.append(
                {
                    "factor": "Contract Complexity",
                    "score": float(complexity_score),
                    "description": f"Large {contract.get_contract_type_display()} contract (€{contract.budget:,.2f})",
                    "risk_level": "high" if complexity_score > 20 else "medium",
                }
            )

        # Contract type
        type_score = self._analyze_contract_type_history(contract)
        if type_score > 5:
            factors.append(
                {
                    "factor": "Contract Type Risk",
                    "score": float(type_score),
                    "description": f"{contract.get_contract_type_display()} contracts historically have delays",
                    "risk_level": "high" if type_score > 15 else "medium",
                }
            )

        # Authority
        authority_score = self._analyze_authority_history(contract)
        if authority_score > 5:
            factors.append(
                {
                    "factor": "Authority Track Record",
                    "score": float(authority_score),
                    "description": f"Authority has history of project delays",
                    "risk_level": "high" if authority_score > 15 else "medium",
                }
            )

        return factors
