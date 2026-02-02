"""
Admin for Point Digital Marketing Manager API.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User,
    AgencySettings,
    AgencySettingsService,
    Quotation,
    QuotationItem,
    Voucher,
    Contract,
    ContractClause,
    ContractClauseLink,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "role", "first_name", "last_name", "is_staff")
    list_filter = ("role", "is_staff")
    fieldsets = BaseUserAdmin.fieldsets + (("Role", {"fields": ("role",)}),)
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Role", {"fields": ("role",)}),
    )


class AgencySettingsServiceInline(admin.TabularInline):
    model = AgencySettingsService
    extra = 0


@admin.register(AgencySettings)
class AgencySettingsAdmin(admin.ModelAdmin):
    inlines = [AgencySettingsServiceInline]
    list_display = ("name", "email", "phone")


class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 0


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    inlines = [QuotationItemInline]
    list_display = ("id", "client_name", "date", "total", "status")
    list_filter = ("status",)


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "amount", "date", "party_name")
    list_filter = ("type",)


class ContractClauseLinkInline(admin.TabularInline):
    model = ContractClauseLink
    extra = 0
    raw_id_fields = ("clause",)


@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    inlines = [ContractClauseLinkInline]
    list_display = ("id", "subject", "date", "total_value", "status")
    list_filter = ("status",)


@admin.register(ContractClause)
class ContractClauseAdmin(admin.ModelAdmin):
    list_display = ("id", "title")
