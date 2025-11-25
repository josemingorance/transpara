"""
Provider analysis model.

Analyzes providers for suspicious patterns, shell companies,
and network connections.
"""
from decimal import Decimal

from django.db.models import Count, Sum

from apps.analytics.ai.base import ProviderAIModel
from apps.contracts.models import Contract
from apps.providers.models import Provider, ProviderRelationship


class ProviderAnalyzer(ProviderAIModel):
    """
    Analyze providers for risk indicators.

    Checks for:
    - New providers winning large contracts
    - Single-customer dependency
    - Rapid growth patterns
    - Suspicious relationships
    - Shell company indicators
    """

    name = "provider_analyzer"

    def calculate_score(self, provider: Provider) -> Decimal:
        """
        Calculate provider risk score.

        Args:
            provider: Provider instance

        Returns:
            Risk score (0-100)
        """
        self.validate_provider(provider)

        risk_score = Decimal("0")

        # Factor 1: Experience check (0-25 points)
        risk_score += self._analyze_experience(provider)

        # Factor 2: Concentration risk (0-25 points)
        risk_score += self._analyze_concentration(provider)

        # Factor 3: Growth patterns (0-20 points)
        risk_score += self._analyze_growth_pattern(provider)

        # Factor 4: Win rate anomaly (0-20 points)
        risk_score += self._analyze_win_rate(provider)

        # Factor 5: Relationship flags (0-10 points)
        risk_score += self._analyze_relationships(provider)

        return risk_score

    def _analyze_experience(self, provider: Provider) -> Decimal:
        """
        Check if provider is new with large contracts.

        Args:
            provider: Provider instance

        Returns:
            Risk score (0-25)
        """
        if not provider.first_contract_date:
            return Decimal("0")

        # Calculate years active
        years_active = provider.years_active or 0

        # New provider with large total amount is suspicious
        if years_active < 1:
            if provider.total_awarded_amount > 1000000:
                return Decimal("25")  # New + large contracts
            elif provider.total_awarded_amount > 100000:
                return Decimal("15")  # New + moderate contracts
            else:
                return Decimal("5")  # New but small contracts

        elif years_active < 2:
            if provider.total_awarded_amount > 5000000:
                return Decimal("20")  # Very rapid growth
            elif provider.total_awarded_amount > 1000000:
                return Decimal("10")  # Rapid growth

        return Decimal("0")

    def _analyze_concentration(self, provider: Provider) -> Decimal:
        """
        Check if provider is dependent on single customer.

        Args:
            provider: Provider instance

        Returns:
            Risk score (0-25)
        """
        # Get distribution of contracts across authorities
        authority_distribution = (
            Contract.objects.filter(awarded_to=provider, status__in=["AWARDED", "COMPLETED"])
            .values("contracting_authority")
            .annotate(count=Count("id"), total=Sum("awarded_amount"))
            .order_by("-total")
        )

        if not authority_distribution:
            return Decimal("0")

        # Check if one authority dominates
        top_authority = authority_distribution[0]
        total_amount = provider.total_awarded_amount

        if total_amount > 0:
            concentration = (
                top_authority["total"] / total_amount
            ) * 100 if top_authority.get("total") else 0

            if concentration > 80:
                return Decimal("25")  # Extreme dependency
            elif concentration > 60:
                return Decimal("18")  # High dependency
            elif concentration > 40:
                return Decimal("10")  # Moderate dependency

        return Decimal("0")

    def _analyze_growth_pattern(self, provider: Provider) -> Decimal:
        """
        Detect abnormal growth patterns.

        Args:
            provider: Provider instance

        Returns:
            Risk score (0-20)
        """
        years_active = provider.years_active or 1

        if years_active == 0:
            return Decimal("0")

        # Average annual revenue
        avg_annual = provider.total_awarded_amount / years_active

        # Suspicious if very high average for short time
        if years_active < 2 and avg_annual > 2000000:
            return Decimal("20")  # Explosive growth
        elif years_active < 3 and avg_annual > 1000000:
            return Decimal("15")  # Rapid growth

        return Decimal("0")

    def _analyze_win_rate(self, provider: Provider) -> Decimal:
        """
        Check if provider has suspiciously high success rate.

        Args:
            provider: Provider instance

        Returns:
            Risk score (0-20)
        """
        success_rate = provider.success_rate

        # Very high win rate can indicate rigged tenders
        if success_rate > 80 and provider.total_contracts > 5:
            return Decimal("20")  # Suspiciously high
        elif success_rate > 70 and provider.total_contracts > 10:
            return Decimal("15")  # Very high
        elif success_rate > 60 and provider.total_contracts > 20:
            return Decimal("10")  # High

        return Decimal("0")

    def _analyze_relationships(self, provider: Provider) -> Decimal:
        """
        Check for suspicious provider relationships.

        Args:
            provider: Provider instance

        Returns:
            Risk score (0-10)
        """
        # Check if provider has flagged relationships
        suspicious_relations = ProviderRelationship.objects.filter(
            Q(provider_a=provider) | Q(provider_b=provider),
            confidence__gt=70,  # High confidence relationships
        ).count()

        if suspicious_relations > 3:
            return Decimal("10")
        elif suspicious_relations > 1:
            return Decimal("7")
        elif suspicious_relations > 0:
            return Decimal("4")

        return Decimal("0")

    def _generate_explanation(self, provider: Provider, score: Decimal) -> str:
        """
        Generate explanation for provider risk score.

        Args:
            provider: Provider instance
            score: Calculated score

        Returns:
            Human-readable explanation
        """
        if score < 20:
            return f"{provider.name} shows normal business patterns"
        elif score < 40:
            return f"{provider.name} shows some unusual patterns worth monitoring"
        elif score < 60:
            return f"{provider.name} shows multiple risk indicators requiring investigation"
        else:
            return f"{provider.name} shows serious red flags suggesting potential shell company or fraud"

    def _get_risk_factors(self, provider: Provider) -> list[dict[str, any]]:
        """
        Get detailed provider risk factors.

        Args:
            provider: Provider instance

        Returns:
            List of risk factor dictionaries
        """
        factors = []

        # Experience
        experience_score = self._analyze_experience(provider)
        if experience_score > 0:
            years = provider.years_active or 0
            factors.append(
                {
                    "factor": "Limited Experience",
                    "score": float(experience_score),
                    "description": f"Provider has {years} year(s) experience but €{provider.total_awarded_amount:,.2f} in contracts",
                    "risk_level": "high" if experience_score > 15 else "medium",
                }
            )

        # Concentration
        concentration_score = self._analyze_concentration(provider)
        if concentration_score > 0:
            factors.append(
                {
                    "factor": "Customer Concentration",
                    "score": float(concentration_score),
                    "description": "Provider is heavily dependent on single contracting authority",
                    "risk_level": "high" if concentration_score > 18 else "medium",
                }
            )

        # Growth
        growth_score = self._analyze_growth_pattern(provider)
        if growth_score > 0:
            factors.append(
                {
                    "factor": "Abnormal Growth",
                    "score": float(growth_score),
                    "description": "Provider shows unusually rapid revenue growth",
                    "risk_level": "high" if growth_score > 15 else "medium",
                }
            )

        # Win rate
        win_rate_score = self._analyze_win_rate(provider)
        if win_rate_score > 0:
            factors.append(
                {
                    "factor": "High Win Rate",
                    "score": float(win_rate_score),
                    "description": f"{provider.success_rate:.1f}% success rate is suspiciously high",
                    "risk_level": "high" if win_rate_score > 15 else "medium",
                }
            )

        # Relationships
        relationship_score = self._analyze_relationships(provider)
        if relationship_score > 0:
            count = ProviderRelationship.objects.filter(
                Q(provider_a=provider) | Q(provider_b=provider)
            ).count()
            factors.append(
                {
                    "factor": "Suspicious Relationships",
                    "score": float(relationship_score),
                    "description": f"Provider has {count} flagged relationship(s)",
                    "risk_level": "medium",
                }
            )

        return factors
