"""
API URL configuration.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet,
    AgencySettingsViewSet,
    QuotationViewSet,
    VoucherViewSet,
    ContractViewSet,
)

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"settings", AgencySettingsViewSet, basename="agencysettings")
router.register(r"quotations", QuotationViewSet, basename="quotation")
router.register(r"vouchers", VoucherViewSet, basename="voucher")
router.register(r"contracts", ContractViewSet, basename="contract")

urlpatterns = [
    path("", include(router.urls)),
]
