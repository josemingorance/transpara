"""
Alert generation service.

Creates alerts for high-risk contracts and providers
based on AI analysis results.
"""
import logging
from typing import Any

from apps.contracts.models import Contract
from apps.providers.models import Provider, ProviderAlert

logger = logging.getLogger(__name__)


class AlertGenerator:
    """
    Generate alerts for suspicious contracts and providers.

    Creates ProviderAlert records when risk thresholds
    are exceeded.
    """

    # Alert thresholds
    CRITICAL_THRESHOLD = 75
    HIGH_THRESHOLD = 60
    MEDIUM_THRESHOLD = 40

    def generate_contract_alerts(
        self, contract: Contract, analysis: dict[str, Any]
    ) -> list[ProviderAlert]:
        """
        Generate alerts based on contract analysis.

        Args:
            contract: Contract instance
            analysis: Risk analysis results

        Returns:
            List of created alerts
        """
        alerts = []

        if not contract.awarded_to:
            return alerts

        # Overall risk alert
        overall_score = analysis["overall"]["score"]
        if overall_score >= self.MEDIUM_THRESHOLD:
            alert = self._create_overall_risk_alert(contract, overall_score, analysis)
            if alert:
                alerts.append(alert)

        # Overpricing alert
        overpricing_score = analysis["overpricing"]["score"]
        if overpricing_score >= self.HIGH_THRESHOLD:
            alert = self._create_overpricing_alert(contract, overpricing_score, analysis)
            if alert:
                alerts.append(alert)

        # Corruption alert
        corruption_score = analysis["corruption"]["score"]
        if corruption_score >= self.HIGH_THRESHOLD:
            alert = self._create_corruption_alert(contract, corruption_score, analysis)
            if alert:
                alerts.append(alert)

        logger.info(f"Generated {len(alerts)} alert(s) for contract {contract.external_id}")

        return alerts

    def generate_provider_alerts(
        self, provider: Provider, analysis: dict[str, Any]
    ) -> list[ProviderAlert]:
        """
        Generate alerts based on provider analysis.

        Args:
            provider: Provider instance
            analysis: Risk analysis results

        Returns:
            List of created alerts
        """
        alerts = []

        score = analysis["score"]

        if score >= self.MEDIUM_THRESHOLD:
            alert = self._create_provider_risk_alert(provider, score, analysis)
            if alert:
                alerts.append(alert)

        logger.info(f"Generated {len(alerts)} alert(s) for provider {provider.name}")

        return alerts

    def _create_overall_risk_alert(
        self, contract: Contract, score: float, analysis: dict[str, Any]
    ) -> ProviderAlert | None:
        """Create alert for overall high risk."""
        severity = self._get_severity(score)

        # Check if similar alert already exists
        existing = ProviderAlert.objects.filter(
            provider=contract.awarded_to,
            alert_type="HIGH_RISK_CONTRACT",
            is_resolved=False,
        ).exists()

        if existing:
            return None

        alert = ProviderAlert.objects.create(
            provider=contract.awarded_to,
            severity=severity,
            alert_type="HIGH_RISK_CONTRACT",
            title=f"High-risk contract detected: {contract.external_id}",
            description=f"Contract shows overall risk score of {score:.1f}/100. {analysis['overall']['explanation']}",
            evidence={
                "contract_id": contract.external_id,
                "contract_title": contract.title,
                "risk_score": score,
                "budget": float(contract.budget),
                "analysis": analysis,
            },
        )

        logger.info(f"Created {severity} alert for contract {contract.external_id}")

        return alert

    def _create_overpricing_alert(
        self, contract: Contract, score: float, analysis: dict[str, Any]
    ) -> ProviderAlert | None:
        """Create alert for significant overpricing."""
        severity = self._get_severity(score)

        # Check if similar alert already exists
        existing = ProviderAlert.objects.filter(
            provider=contract.awarded_to,
            alert_type="OVERPRICING",
            is_resolved=False,
        ).exists()

        if existing:
            return None

        alert = ProviderAlert.objects.create(
            provider=contract.awarded_to,
            severity=severity,
            alert_type="OVERPRICING",
            title=f"Overpricing detected: {contract.external_id}",
            description=f"Contract price is significantly above market rates (score: {score:.1f}/100). {analysis['overpricing']['explanation']}",
            evidence={
                "contract_id": contract.external_id,
                "contract_title": contract.title,
                "overpricing_score": score,
                "budget": float(contract.budget),
                "awarded_amount": float(contract.awarded_amount) if contract.awarded_amount else None,
                "factors": analysis["overpricing"].get("factors", []),
            },
        )

        return alert

    def _create_corruption_alert(
        self, contract: Contract, score: float, analysis: dict[str, Any]
    ) -> ProviderAlert | None:
        """Create alert for corruption risk indicators."""
        severity = self._get_severity(score)

        # Check if similar alert already exists
        existing = ProviderAlert.objects.filter(
            provider=contract.awarded_to,
            alert_type="CORRUPTION_INDICATORS",
            is_resolved=False,
        ).exists()

        if existing:
            return None

        alert = ProviderAlert.objects.create(
            provider=contract.awarded_to,
            severity=severity,
            alert_type="CORRUPTION_INDICATORS",
            title=f"Corruption risk indicators: {contract.external_id}",
            description=f"Contract shows multiple corruption risk patterns (score: {score:.1f}/100). {analysis['corruption']['explanation']}",
            evidence={
                "contract_id": contract.external_id,
                "contract_title": contract.title,
                "corruption_score": score,
                "factors": analysis["corruption"].get("factors", []),
            },
        )

        return alert

    def _create_provider_risk_alert(
        self, provider: Provider, score: float, analysis: dict[str, Any]
    ) -> ProviderAlert | None:
        """Create alert for provider risk."""
        severity = self._get_severity(score)

        # Check if similar alert already exists
        existing = ProviderAlert.objects.filter(
            provider=provider,
            alert_type="PROVIDER_RISK",
            is_resolved=False,
        ).exists()

        if existing:
            return None

        alert = ProviderAlert.objects.create(
            provider=provider,
            severity=severity,
            alert_type="PROVIDER_RISK",
            title=f"High-risk provider: {provider.name}",
            description=f"Provider shows suspicious patterns (score: {score:.1f}/100). {analysis['explanation']}",
            evidence={
                "provider_tax_id": provider.tax_id,
                "risk_score": score,
                "factors": analysis.get("factors", []),
            },
        )

        return alert

    def _get_severity(self, score: float) -> str:
        """
        Determine alert severity based on score.

        Args:
            score: Risk score

        Returns:
            Severity level
        """
        if score >= self.CRITICAL_THRESHOLD:
            return "CRITICAL"
        elif score >= self.HIGH_THRESHOLD:
            return "HIGH"
        elif score >= self.MEDIUM_THRESHOLD:
            return "MEDIUM"
        else:
            return "LOW"
