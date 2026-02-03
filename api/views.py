"""
ViewSets for Point Digital Marketing Manager API.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model

from .models import (
    AgencySettings,
    Quotation,
    Voucher,
    Contract,
    SMSLog,
)
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    AgencySettingsSerializer,
    QuotationSerializer,
    VoucherSerializer,
    ContractSerializer,
    SMSLogSerializer,
)
from .permissions import (
    IsAdminUser,
    IsAccountantReadAddOrAdmin,
    _is_accountant,
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """List/retrieve/create for authenticated (incl. ACCOUNTANT); update/delete for ADMIN only."""

    queryset = User.objects.all().order_by("-date_joined")
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve", "me", "create"):
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminUser()]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = UserSerializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        """Return current authenticated user (for frontend after JWT login)."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class AgencySettingsViewSet(viewsets.ModelViewSet):
    """CRUD for agency settings. Only ADMIN can access (read/write). Accountant has no access."""

    queryset = AgencySettings.objects.all()
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = AgencySettingsSerializer


class QuotationViewSet(viewsets.ModelViewSet):
    """Accountant: read + add only. Admin: full CRUD. set_status is update → admin only."""

    queryset = Quotation.objects.all()
    permission_classes = [IsAuthenticated, IsAccountantReadAddOrAdmin]
    serializer_class = QuotationSerializer

    def get_permissions(self):
        if self.action == "set_status":
            return [IsAuthenticated(), IsAdminUser()]
        return [IsAuthenticated(), IsAccountantReadAddOrAdmin()]

    @action(detail=True, methods=["post"])
    def set_status(self, request, pk=None):
        """Update quotation status (PENDING, ACCEPTED, REJECTED). Admin only."""
        quotation = self.get_object()
        new_status = request.data.get("status")
        if new_status not in dict(Quotation.Status.choices):
            return Response(
                {"status": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST
            )
        quotation.status = new_status
        quotation.save()
        serializer = self.get_serializer(quotation)
        return Response(serializer.data)


class VoucherViewSet(viewsets.ModelViewSet):
    """Accountant: read + add only, and no access to OWNER_WITHDRAWAL. Admin: full CRUD."""

    queryset = Voucher.objects.all()
    permission_classes = [IsAuthenticated, IsAccountantReadAddOrAdmin]
    serializer_class = VoucherSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        if _is_accountant(self.request.user):
            return qs.exclude(category=Voucher.Category.OWNER_WITHDRAWAL)
        return qs

    def perform_create(self, serializer):
        if _is_accountant(self.request.user):
            category = serializer.validated_data.get("category")
            if category == Voucher.Category.OWNER_WITHDRAWAL:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("المحاسب لا يملك صلاحية إنشاء سحوبات المالك.")
        serializer.save()


class ContractViewSet(viewsets.ModelViewSet):
    """Accountant: read + add only. Admin: full CRUD."""

    queryset = Contract.objects.all()
    permission_classes = [IsAuthenticated, IsAccountantReadAddOrAdmin]
    serializer_class = ContractSerializer


class SMSLogViewSet(viewsets.ModelViewSet):
    """Accountant: read + add only. Admin: full access including delete."""

    queryset = SMSLog.objects.all()
    permission_classes = [IsAuthenticated, IsAccountantReadAddOrAdmin]
    serializer_class = SMSLogSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]
