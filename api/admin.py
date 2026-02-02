"""
Admin for Point Digital Marketing Manager API.
All models are registered so they appear in the admin panel.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User,
    ServiceDefinition,
    AgencySettings,
    AgencySettingsService,
    ServiceItem,
    Quotation,
    QuotationItem,
    Voucher,
    Contract,
    ContractClause,
    ContractClauseLink,
    SMSLog,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "role", "first_name", "last_name", "is_staff")
    list_filter = ("role", "is_staff")
    fieldsets = BaseUserAdmin.fieldsets + (("Role", {"fields": ("role",)}),)
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Role", {"fields": ("role",)}),
    )


@admin.register(ServiceDefinition)
class ServiceDefinitionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "description")
    search_fields = ("name",)


class AgencySettingsServiceInline(admin.TabularInline):
    model = AgencySettingsService
    extra = 0


@admin.register(AgencySettings)
class AgencySettingsAdmin(admin.ModelAdmin):
    inlines = [AgencySettingsServiceInline]
    list_display = ("id", "name", "email", "phone")
    search_fields = ("name", "email")


@admin.register(AgencySettingsService)
class AgencySettingsServiceAdmin(admin.ModelAdmin):
    list_display = ("id", "settings", "name", "description")
    list_filter = ("settings",)
    search_fields = ("name",)
    raw_id_fields = ("settings",)


@admin.register(ServiceItem)
class ServiceItemAdmin(admin.ModelAdmin):
    list_display = ("id", "description", "price", "quantity")
    search_fields = ("description",)


class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 0


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    inlines = [QuotationItemInline]
    list_display = ("id", "client_name", "date", "total", "status")
    list_filter = ("status",)
    search_fields = ("client_name",)


@admin.register(QuotationItem)
class QuotationItemAdmin(admin.ModelAdmin):
    list_display = ("id", "quotation", "description", "price", "quantity")
    list_filter = ("quotation",)
    search_fields = ("description",)
    raw_id_fields = ("quotation",)


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "amount", "date", "party_name")
    list_filter = ("type",)
    search_fields = ("party_name", "description")


class ContractClauseLinkInline(admin.TabularInline):
    model = ContractClauseLink
    extra = 0
    raw_id_fields = ("clause",)


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    inlines = [ContractClauseLinkInline]
    list_display = ("id", "subject", "date", "total_value", "status")
    list_filter = ("status",)
    search_fields = ("subject", "party_a_name", "party_b_name")


@admin.register(ContractClause)
class ContractClauseAdmin(admin.ModelAdmin):
    list_display = ("id", "title")
    search_fields = ("title", "content")


@admin.register(ContractClauseLink)
class ContractClauseLinkAdmin(admin.ModelAdmin):
    list_display = ("id", "contract", "clause", "order")
    list_filter = ("contract",)
    raw_id_fields = ("contract", "clause")
    ordering = ("contract", "order")


@admin.register(SMSLog)
class SMSLogAdmin(admin.ModelAdmin):
    list_display = ("id", "to", "status", "timestamp")
    list_filter = ("status",)
    search_fields = ("to", "body")
    readonly_fields = ("timestamp",)
