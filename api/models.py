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
    """Singleton-like agency settings (v4: + twilio, exchange_rate)."""

    name = models.CharField(max_length=255)
    logo = models.TextField(blank=True)  # URL or base64 data URL (for uploaded images)
    address = models.CharField(max_length=500, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    quotation_terms = models.JSONField(default=list)  # list of strings
    twilio = models.JSONField(default=dict, blank=True)  # { accountSid, authToken, fromNumber, senderName, isEnabled }
    exchange_rate = models.DecimalField(max_digits=14, decimal_places=2, default=1500)

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
    """Quotation: client, date, items, total, status, note (v4: client_phone, currency)."""

    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        ACCEPTED = "ACCEPTED", _("Accepted")
        REJECTED = "REJECTED", _("Rejected")

    id = models.CharField(primary_key=True, max_length=36, editable=False, default=uuid.uuid4)
    client_name = models.CharField(max_length=255)
    client_phone = models.CharField(max_length=50, blank=True)
    date = models.CharField(max_length=50)  # frontend uses locale date string
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="IQD")  # IQD / USD
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "api_quotation"
        ordering = ["-created_at"]


class QuotationItem(models.Model):
    """Quotation line item linked to a quotation (v4: optional currency)."""

    id = models.CharField(primary_key=True, max_length=36, editable=False, default=uuid.uuid4)
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="items")
    description = models.TextField()
    price = models.DecimalField(max_digits=14, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    currency = models.CharField(max_length=3, blank=True, default="")

    class Meta:
        db_table = "api_quotation_item"


class Voucher(models.Model):
    """Voucher (v4): type RECEIPT/PAYMENT, currency, party_phone, category."""

    class VoucherType(models.TextChoices):
        RECEIPT = "RECEIPT", _("قبض")
        PAYMENT = "PAYMENT", _("صرف")

    class Category(models.TextChoices):
        SALARY = "SALARY", _("راتب")
        DAILY = "DAILY", _("يومي")
        GENERAL = "GENERAL", _("عام")
        VOUCHER = "VOUCHER", _("وصل")

    id = models.CharField(primary_key=True, max_length=36, editable=False, default=uuid.uuid4)
    type = models.CharField(max_length=20, choices=VoucherType.choices)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default="IQD")
    date = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    party_name = models.CharField(max_length=255)
    party_phone = models.CharField(max_length=50, blank=True)
    category = models.CharField(max_length=20, choices=Category.choices, blank=True)
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
    """Contract (v4): status ACTIVE/ARCHIVED, currency."""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", _("Active")
        ARCHIVED = "ARCHIVED", _("Archived")

    id = models.CharField(primary_key=True, max_length=36, editable=False, default=uuid.uuid4)
    date = models.CharField(max_length=50)
    party_a_name = models.CharField(max_length=255)
    party_a_title = models.CharField(max_length=255, blank=True)
    party_b_name = models.CharField(max_length=255)
    party_b_title = models.CharField(max_length=255, blank=True)
    subject = models.CharField(max_length=500)
    total_value = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="IQD")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
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


class SMSLog(models.Model):
    """SMS log (v4): to, body, status, timestamp, error."""

    class LogStatus(models.TextChoices):
        SUCCESS = "SUCCESS", _("Success")
        FAILED = "FAILED", _("Failed")

    id = models.CharField(primary_key=True, max_length=36, editable=False, default=uuid.uuid4)
    to = models.CharField(max_length=50)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=LogStatus.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    error = models.TextField(blank=True)

    class Meta:
        db_table = "api_sms_log"
        ordering = ["-timestamp"]
