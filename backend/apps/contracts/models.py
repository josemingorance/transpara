"""Contract models."""
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import SoftDeleteModel


class ContractType(models.TextChoices):
    """Types of public contracts."""

    WORKS = "WORKS", "Works"
    SERVICES = "SERVICES", "Services"
    SUPPLIES = "SUPPLIES", "Supplies"
    MIXED = "MIXED", "Mixed"
    OTHER = "OTHER", "Other"


class ContractStatus(models.TextChoices):
    """Status of a contract."""

    DRAFT = "DRAFT", "Draft"
    PUBLISHED = "PUBLISHED", "Published"
    IN_PROGRESS = "IN_PROGRESS", "In Progress"
    AWARDED = "AWARDED", "Awarded"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


class ProcedureType(models.TextChoices):
    """Types of procurement procedures."""

    OPEN = "OPEN", "Open"
    RESTRICTED = "RESTRICTED", "Restricted"
    NEGOTIATED = "NEGOTIATED", "Negotiated"
    COMPETITIVE_DIALOGUE = "COMPETITIVE_DIALOGUE", "Competitive Dialogue"
    MINOR = "MINOR", "Minor Contract"


class Contract(SoftDeleteModel):
    """
    Public contract model.

    Represents a public procurement contract with all relevant
    information including budget, timeline, and risk analysis.
    """

    # Basic Information
    title = models.CharField(max_length=1000, db_index=True)
    description = models.TextField(blank=True)
    contract_type = models.CharField(
        max_length=20, choices=ContractType.choices, db_index=True
    )
    status = models.CharField(
        max_length=20, choices=ContractStatus.choices, default=ContractStatus.DRAFT, db_index=True
    )

    # Financial
    budget = models.DecimalField(
        max_digits=15, decimal_places=2, help_text="Budget in EUR", db_index=True
    )
    awarded_amount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True, help_text="Final awarded amount"
    )

    # Procurement
    procedure_type = models.CharField(max_length=30, choices=ProcedureType.choices, db_index=True)
    publication_date = models.DateField(null=True, blank=True, db_index=True)
    deadline_date = models.DateField(null=True, blank=True, db_index=True)
    award_date = models.DateField(null=True, blank=True, db_index=True)

    # Entities
    contracting_authority = models.CharField(max_length=300, db_index=True)
    awarded_to = models.ForeignKey(
        "providers.Provider",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contracts",
    )

    # Location
    region = models.CharField(max_length=100, db_index=True)
    province = models.CharField(max_length=100, blank=True, db_index=True)
    municipality = models.CharField(max_length=100, blank=True, db_index=True)

    # Source & External References
    source_url = models.URLField(max_length=500, blank=True)
    external_id = models.CharField(max_length=200, unique=True, db_index=True)
    source_platform = models.CharField(max_length=100, db_index=True)

    # Risk Analysis (calculated by AI engine)
    risk_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
        help_text="Overall risk score (0-100)",
    )
    corruption_risk = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )
    delay_risk = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )
    financial_risk = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
    )

    # Flags
    is_overpriced = models.BooleanField(default=False, db_index=True)
    has_amendments = models.BooleanField(default=False)
    has_delays = models.BooleanField(default=False)

    # Analysis metadata
    analyzed_at = models.DateTimeField(null=True, blank=True, db_index=True)
    analysis_version = models.CharField(max_length=20, blank=True)

    class Meta:
        verbose_name = "Contract"
        verbose_name_plural = "Contracts"
        ordering = ["-publication_date", "-created_at"]
        indexes = [
            models.Index(fields=["status", "publication_date"]),
            models.Index(fields=["region", "contract_type"]),
            models.Index(fields=["risk_score"]),
        ]

    def __str__(self) -> str:
        return f"{self.external_id} - {self.title[:50]}"

    @property
    def overpricing_percentage(self) -> Decimal | None:
        """Calculate overpricing if contract is awarded."""
        if self.awarded_amount and self.budget:
            return ((self.awarded_amount - self.budget) / self.budget) * 100
        return None

    @property
    def has_high_risk(self) -> bool:
        """Check if contract has high overall risk (>70)."""
        return self.risk_score and self.risk_score > 70


class ContractAmendment(SoftDeleteModel):
    """
    Contract amendments and modifications.

    Tracks changes made to contracts after award,
    which can indicate issues or irregularities.
    """

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="amendments")
    amendment_type = models.CharField(max_length=100)
    description = models.TextField()
    previous_amount = models.DecimalField(max_digits=15, decimal_places=2)
    new_amount = models.DecimalField(max_digits=15, decimal_places=2)
    amendment_date = models.DateField(db_index=True)
    reason = models.TextField(blank=True)

    class Meta:
        verbose_name = "Contract Amendment"
        verbose_name_plural = "Contract Amendments"
        ordering = ["-amendment_date"]

    def __str__(self) -> str:
        return f"Amendment to {self.contract.external_id} on {self.amendment_date}"

    @property
    def amount_change_percentage(self) -> Decimal:
        """Calculate percentage change in amount."""
        if self.previous_amount:
            return ((self.new_amount - self.previous_amount) / self.previous_amount) * 100
        return Decimal("0")


class RawContractData(SoftDeleteModel):
    """
    Raw data from crawlers before normalization.

    Stores the original data as extracted from sources,
    useful for debugging and re-processing.
    """

    source_platform = models.CharField(max_length=100, db_index=True)
    external_id = models.CharField(max_length=200, db_index=True)
    raw_data = models.JSONField()
    source_url = models.URLField(max_length=500, blank=True)

    # Processing status
    is_processed = models.BooleanField(default=False, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processing_error = models.TextField(blank=True)

    # Link to normalized contract
    contract = models.ForeignKey(
        Contract, on_delete=models.SET_NULL, null=True, blank=True, related_name="raw_data"
    )

    class Meta:
        verbose_name = "Raw Contract Data"
        verbose_name_plural = "Raw Contract Data"
        unique_together = [["source_platform", "external_id"]]
        indexes = [
            models.Index(fields=["is_processed", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.source_platform} - {self.external_id}"
