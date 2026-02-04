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
    FreelancerViewSet,
    FreelanceWorkViewSet,
    SMSLogViewSet,
    send_sms,
)

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"settings", AgencySettingsViewSet, basename="agencysettings")
router.register(r"quotations", QuotationViewSet, basename="quotation")
router.register(r"vouchers", VoucherViewSet, basename="voucher")
router.register(r"contracts", ContractViewSet, basename="contract")
router.register(r"freelancers", FreelancerViewSet, basename="freelancer")
router.register(r"freelance-works", FreelanceWorkViewSet, basename="freelancework")
router.register(r"sms-logs", SMSLogViewSet, basename="smslog")

urlpatterns = [
    path("send-sms/", send_sms),
    path("", include(router.urls)),
]
