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
from .permissions import IsAuthenticatedReadOnlyOrAdmin, IsAdminUser

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """CRUD for users. List/retrieve for authenticated; create/update/delete for ADMIN only."""

    queryset = User.objects.all().order_by("-date_joined")
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve", "me"):
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
    """CRUD for agency settings. Write only for ADMIN."""

    queryset = AgencySettings.objects.all()
    permission_classes = [IsAuthenticated, IsAuthenticatedReadOnlyOrAdmin]
    serializer_class = AgencySettingsSerializer


class QuotationViewSet(viewsets.ModelViewSet):
    """CRUD for quotations."""

    queryset = Quotation.objects.all()
    permission_classes = [IsAuthenticated, IsAuthenticatedReadOnlyOrAdmin]
    serializer_class = QuotationSerializer

    @action(detail=True, methods=["post"])
    def set_status(self, request, pk=None):
        """Update quotation status (PENDING, ACCEPTED, REJECTED)."""
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
    """CRUD for vouchers."""

    queryset = Voucher.objects.all()
    permission_classes = [IsAuthenticated, IsAuthenticatedReadOnlyOrAdmin]
    serializer_class = VoucherSerializer


class ContractViewSet(viewsets.ModelViewSet):
    """CRUD for contracts (v4: status ACTIVE/ARCHIVED)."""

    queryset = Contract.objects.all()
    permission_classes = [IsAuthenticated, IsAuthenticatedReadOnlyOrAdmin]
    serializer_class = ContractSerializer


class SMSLogViewSet(viewsets.ModelViewSet):
    """CRUD for SMS logs (v4). List/create for authenticated; delete for ADMIN."""

    queryset = SMSLog.objects.all()
    permission_classes = [IsAuthenticated, IsAuthenticatedReadOnlyOrAdmin]
    serializer_class = SMSLogSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]
