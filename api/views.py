"""
ViewSets for Point Digital Marketing Manager API.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_sms(request):
    """
    Send SMS via Twilio using agency settings. Body: { "to": "+964...", "body": "text" }.
    Credentials stay on server; avoids CORS and client exposure.
    """
    to = (request.data.get("to") or "").strip()
    body = (request.data.get("body") or "").strip()
    if not to or not body:
        return Response(
            {"success": False, "error": "يجب تحديد رقم المستلم ونص الرسالة."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    settings_obj = AgencySettings.objects.first()
    if not settings_obj or not settings_obj.twilio:
        return Response(
            {"success": False, "error": "إعدادات Twilio غير متوفرة. احفظ الإعدادات من صفحة الإعدادات (مدير النظام) مع تفعيل ربط Twilio."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    twilio_config = settings_obj.twilio or {}
    # دعم camelCase و snake_case
    is_enabled = twilio_config.get("isEnabled", twilio_config.get("is_enabled", False))
    if not is_enabled:
        return Response(
            {"success": False, "error": "إرسال الرسائل معطل في الإعدادات. فعّل «الربط مفعل» في الإعدادات."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    account_sid = (twilio_config.get("accountSid") or twilio_config.get("account_sid") or "").strip()
    auth_token = (twilio_config.get("authToken") or twilio_config.get("auth_token") or "").strip()
    from_number = (twilio_config.get("fromNumber") or twilio_config.get("from_number") or "").strip()
    sender_name = (twilio_config.get("senderName") or twilio_config.get("sender_name") or "").strip()
    # يمكن استخدام رقم المرسل أو Sender ID (اسم المرسل) فقط
    from_value = from_number if from_number else sender_name
    if not account_sid or not auth_token:
        missing = []
        if not account_sid:
            missing.append("Account SID")
        if not auth_token:
            missing.append("Auth Token")
        return Response(
            {
                "success": False,
                "error": "بيانات Twilio ناقصة: " + "، ".join(missing) + ". ادخلها من الإعدادات > ربط إشعارات SMS (Twilio) واحفظ الصفحة."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not from_value:
        return Response(
            {
                "success": False,
                "error": "يجب إدخال رقم المرسل أو اسم المرسل (Sender ID) في الإعدادات. يمكنك ترك رقم المرسل فارغاً واستخدام اسم المرسل فقط."
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    # تنسيق رقم الهاتف
    if to.startswith("07") and len(to) >= 10:
        to = "+964" + to[1:]
    elif not to.startswith("+"):
        to = "+" + to
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        message = client.messages.create(body=body, from_=from_value, to=to)
        if message.sid:
            return Response({"success": True})
        return Response(
            {"success": False, "error": "لم يتم إرجاع معرف الرسالة من Twilio."},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    except Exception as e:
        import re
        err_msg = str(e)
        err_msg = re.sub(r"\x1b\[[0-9;]*m", "", err_msg).strip()
        # رسالة مبسطة للحالات الشائعة
        if "inactive" in err_msg.lower() or "90010" in err_msg:
            err_msg = "حساب Twilio غير نشط. فعّل الحساب من لوحة Twilio (Console) أو استخدم حساباً آخر. تفاصيل: https://www.twilio.com/docs/errors/90010"
        elif "authenticate" in err_msg.lower() or "20003" in err_msg:
            err_msg = "بيانات Twilio غير صحيحة (Account SID أو Auth Token). تحقق من الإعدادات."
        elif "21606" in err_msg or ("not a valid message-capable" in err_msg and "From" in err_msg):
            err_msg = "اسم المرسل (Sender ID) غير مدعوم لهذا البلد. استخدم «رقم المرسل» في الإعدادات بدلاً من الاعتماد على الاسم فقط، أو راجع: https://www.twilio.com/docs/errors/21606"
        elif "21211" in err_msg or "invalid" in err_msg.lower() and "to" in err_msg.lower():
            err_msg = "رقم المستلم غير صالح. استخدم صيغة دولية مثل +9647xxxxxxxx"
        return Response(
            {"success": False, "error": err_msg},
            status=status.HTTP_502_BAD_GATEWAY,
        )
