"""
Models for Point Digital Marketing Manager API.
Aligned with frontend types (User, Quotation, Voucher, Contract, AgencySettings).
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom user with role (ADMIN / ACCOUNTANT)."""

    class Role(models.TextChoices):
        ADMIN = "ADMIN", _("مدير نظام")
        ACCOUNTANT = "ACCOUNTANT", _("محاسب")

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ACCOUNTANT)

    class Meta:
        db_table = "api_user"
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return self.username


class ServiceDefinition(models.Model):
    """Inline service definition for agency settings (name, description)."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "api_service_definition"


class AgencySettings(models.Model):
    """Singleton-like agency settings (name, logo, address, services, quotation terms)."""

    name = models.CharField(max_length=255)
    logo = models.TextField(blank=True)  # URL or base64 data URL (for uploaded images)
    address = models.CharField(max_length=500, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    quotation_terms = models.JSONField(default=list)  # list of strings

    class Meta:
        db_table = "api_agency_settings"
        verbose_name_plural = _("Agency settings")
        ordering = ["id"]

    def __str__(self):
        return self.name


class AgencySettingsService(models.Model):
    """Many-to-many style: services belonging to an agency settings record."""

    settings = models.ForeignKey(AgencySettings, on_delete=models.CASCADE, related_name="services_fk")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "api_agency_settings_service"


class ServiceItem(models.Model):
    """Line item for a quotation (description, price, quantity)."""

    id = models.CharField(primary_key=True, max_length=36, editable=False, default=uuid.uuid4)
    description = models.TextField()
    price = models.DecimalField(max_digits=14, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "api_service_item"


class Quotation(models.Model):
    """Quotation: client, date, items, total, status, note."""

    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        ACCEPTED = "ACCEPTED", _("Accepted")
        REJECTED = "REJECTED", _("Rejected")

    id = models.CharField(primary_key=True, max_length=36, editable=False, default=uuid.uuid4)
    client_name = models.CharField(max_length=255)
    date = models.CharField(max_length=50)  # frontend uses locale date string
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "api_quotation"
        ordering = ["-created_at"]


class QuotationItem(models.Model):
    """Quotation line item linked to a quotation."""

    id = models.CharField(primary_key=True, max_length=36, editable=False, default=uuid.uuid4)
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="items")
    description = models.TextField()
    price = models.DecimalField(max_digits=14, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "api_quotation_item"


class Voucher(models.Model):
    """Voucher: type (RECEIPT/EXPENDITURE), amount, date, description, party_name."""

    class VoucherType(models.TextChoices):
        RECEIPT = "RECEIPT", _("قبض")
        EXPENDITURE = "EXPENDITURE", _("صرف")

    id = models.CharField(primary_key=True, max_length=36, editable=False, default=uuid.uuid4)
    type = models.CharField(max_length=20, choices=VoucherType.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    date = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    party_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "api_voucher"
        ordering = ["-created_at"]


class ContractClause(models.Model):
    """Contract clause: title, content."""

    id = models.CharField(primary_key=True, max_length=36, editable=False, default=uuid.uuid4)
    title = models.CharField(max_length=255)
    content = models.TextField()

    class Meta:
        db_table = "api_contract_clause"


class Contract(models.Model):
    """Contract: parties, subject, value, clauses, status."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        EXPIRED = "EXPIRED", _("Expired")
        DRAFT = "DRAFT", _("Draft")

    id = models.CharField(primary_key=True, max_length=36, editable=False, default=uuid.uuid4)
    date = models.CharField(max_length=50)
    party_a_name = models.CharField(max_length=255)
    party_a_title = models.CharField(max_length=255, blank=True)
    party_b_name = models.CharField(max_length=255)
    party_b_title = models.CharField(max_length=255, blank=True)
    subject = models.CharField(max_length=500)
    total_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "api_contract"
        ordering = ["-created_at"]


class ContractClauseLink(models.Model):
    """Links contract to its clauses (order preserved by creation)."""

    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name="clause_links")
    clause = models.ForeignKey(ContractClause, on_delete=models.CASCADE, related_name="contract_links")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "api_contract_clause_link"
        ordering = ["order"]
