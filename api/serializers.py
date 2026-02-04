"""
Serializers for Point Digital Marketing Manager API.
Output format matches frontend types (camelCase handled via to_representation where needed).
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model

from .id_utils import get_next_id
from .models import (
    AgencySettings,
    AgencySettingsService,
    Quotation,
    QuotationItem,
    Voucher,
    Contract,
    ContractClause,
    ContractClauseLink,
    Freelancer,
    FreelanceWork,
    SMSLog,
)

User = get_user_model()


# ----- User -----
class UserSerializer(serializers.ModelSerializer):
    """User serializer; id as string, role as enum string."""

    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    createdAt = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "name", "username", "role", "createdAt"]
        read_only_fields = ["id", "username", "createdAt"]
        extra_kwargs = {"password": {"write_only": True}}

    def get_id(self, obj):
        return str(obj.pk)

    def get_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_createdAt(self, obj):
        return obj.date_joined.strftime("%Y-%m-%d") if obj.date_joined else ""

    def update(self, instance, validated_data):
        name = validated_data.pop("name", None)
        if name is not None:
            parts = (name or "").strip().split(None, 1)
            instance.first_name = parts[0] if parts else ""
            instance.last_name = parts[1] if len(parts) > 1 else ""
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UserCreateSerializer(serializers.ModelSerializer):
    """Create user with name (first_name used as display name)."""

    name = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["name", "username", "password", "role"]

    def create(self, validated_data):
        name = validated_data.pop("name", "")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        parts = name.strip().split(None, 1)
        user.first_name = parts[0] if parts else ""
        user.last_name = parts[1] if len(parts) > 1 else ""
        user.save()
        return user


# ----- Agency Settings -----
class ServiceDefinitionSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)


class AgencySettingsSerializer(serializers.ModelSerializer):
    services = ServiceDefinitionSerializer(many=True, required=False)
    quotationTerms = serializers.ListField(
        child=serializers.CharField(), source="quotation_terms", required=False
    )
    twilio = serializers.JSONField(required=False, default=dict)
    exchangeRate = serializers.DecimalField(
        max_digits=14, decimal_places=2, source="exchange_rate", required=False
    )

    class Meta:
        model = AgencySettings
        fields = [
            "id",
            "name",
            "logo",
            "address",
            "phone",
            "email",
            "services",
            "quotationTerms",
            "twilio",
            "exchangeRate",
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["services"] = [
            {"name": s.name, "description": s.description or ""}
            for s in instance.services_fk.all().order_by("id")
        ]
        rep["quotationTerms"] = instance.quotation_terms or []
        rep["twilio"] = instance.twilio or {}
        rep["exchangeRate"] = float(instance.exchange_rate) if instance.exchange_rate else 1500
        return rep

    def create(self, validated_data):
        services_data = validated_data.pop("services", [])
        quotation_terms = validated_data.pop("quotation_terms", [])
        exchange_rate = validated_data.pop("exchange_rate", 1500)
        twilio = validated_data.pop("twilio", {})
        settings = AgencySettings.objects.create(
            quotation_terms=quotation_terms,
            exchange_rate=exchange_rate,
            twilio=twilio,
            **validated_data,
        )
        for s in services_data:
            AgencySettingsService.objects.create(settings=settings, **s)
        return settings

    def update(self, instance, validated_data):
        services_data = validated_data.pop("services", None)
        quotation_terms = validated_data.get("quotation_terms")
        if quotation_terms is not None:
            instance.quotation_terms = quotation_terms
        if "exchange_rate" in validated_data:
            instance.exchange_rate = validated_data.pop("exchange_rate")
        if "twilio" in validated_data:
            instance.twilio = validated_data.pop("twilio")
        for attr, value in validated_data.items():
            if attr not in ("quotation_terms", "exchange_rate", "twilio"):
                setattr(instance, attr, value)
        instance.save()
        if services_data is not None:
            instance.services_fk.all().delete()
            for s in services_data:
                AgencySettingsService.objects.create(settings=instance, **s)
        return instance


# ----- Quotation -----
class QuotationItemSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    currency = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = QuotationItem
        fields = ["id", "description", "price", "quantity", "currency"]


class QuotationSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    clientName = serializers.CharField(source="client_name")
    clientPhone = serializers.CharField(source="client_phone", required=False, allow_blank=True)
    items = QuotationItemSerializer(many=True, required=False)
    currency = serializers.CharField(required=False, default="IQD")
    status = serializers.ChoiceField(choices=Quotation.Status.choices)

    class Meta:
        model = Quotation
        fields = ["id", "clientName", "clientPhone", "date", "items", "total", "currency", "status", "note"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["items"] = QuotationItemSerializer(instance.items.all().order_by("id"), many=True).data
        return rep

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        validated_data["client_name"] = validated_data.pop("client_name")
        validated_data["client_phone"] = validated_data.pop("client_phone", "") or ""
        validated_data.setdefault("currency", "IQD")
        validated_data["id"] = get_next_id("QT", Quotation)
        quotation = Quotation.objects.create(**validated_data)
        total = 0
        for item in items_data:
            item.pop("id", None)
            item.setdefault("currency", "")
            item["id"] = get_next_id("QI", QuotationItem)
            qi = QuotationItem.objects.create(quotation=quotation, **item)
            total += float(qi.price) * qi.quantity
        quotation.total = total
        quotation.save()
        return quotation

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", None)
        if "client_name" in validated_data:
            instance.client_name = validated_data.pop("client_name")
        if "client_phone" in validated_data:
            instance.client_phone = validated_data.pop("client_phone", "") or ""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if items_data is not None:
            instance.items.all().delete()
            total = 0
            for item in items_data:
                item.pop("id", None)
                item.setdefault("currency", "")
                item["id"] = get_next_id("QI", QuotationItem)
                qi = QuotationItem.objects.create(quotation=instance, **item)
                total += float(qi.price) * qi.quantity
            instance.total = total
        instance.save()
        return instance


# ----- Voucher -----
class VoucherSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    type = serializers.ChoiceField(choices=Voucher.VoucherType.choices)
    partyName = serializers.CharField(source="party_name")
    partyPhone = serializers.CharField(source="party_phone", required=False, allow_blank=True)
    currency = serializers.CharField(required=False, default="IQD")
    category = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Voucher
        fields = ["id", "type", "amount", "currency", "date", "description", "partyName", "partyPhone", "category"]

    def create(self, validated_data):
        validated_data["party_name"] = validated_data.pop("party_name")
        validated_data["party_phone"] = validated_data.pop("party_phone", "") or ""
        validated_data.setdefault("currency", "IQD")
        validated_data.setdefault("category", "")
        validated_data["id"] = get_next_id("VC", Voucher)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "party_name" in validated_data:
            instance.party_name = validated_data.pop("party_name")
        if "party_phone" in validated_data:
            instance.party_phone = validated_data.pop("party_phone", "") or ""
        return super().update(instance, validated_data)


# ----- Contract -----
class ContractClauseSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)

    class Meta:
        model = ContractClause
        fields = ["id", "title", "content"]


class ContractSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    partyAName = serializers.CharField(source="party_a_name")
    partyATitle = serializers.CharField(source="party_a_title", required=False, allow_blank=True)
    partyBName = serializers.CharField(source="party_b_name")
    partyBTitle = serializers.CharField(source="party_b_title", required=False, allow_blank=True)
    totalValue = serializers.DecimalField(
        max_digits=14, decimal_places=2, source="total_value"
    )
    currency = serializers.CharField(required=False, default="IQD")
    clauses = ContractClauseSerializer(many=True, required=False)
    status = serializers.ChoiceField(choices=Contract.Status.choices)

    class Meta:
        model = Contract
        fields = [
            "id",
            "date",
            "partyAName",
            "partyATitle",
            "partyBName",
            "partyBTitle",
            "subject",
            "totalValue",
            "currency",
            "clauses",
            "status",
        ]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        links = instance.clause_links.all().order_by("order")
        rep["clauses"] = [
            ContractClauseSerializer(link.clause).data for link in links
        ]
        return rep

    def create(self, validated_data):
        clauses_data = validated_data.pop("clauses", [])
        validated_data["party_a_name"] = validated_data.pop("party_a_name")
        validated_data["party_a_title"] = validated_data.pop("party_a_title", "") or ""
        validated_data["party_b_name"] = validated_data.pop("party_b_name")
        validated_data["party_b_title"] = validated_data.pop("party_b_title", "") or ""
        validated_data["total_value"] = validated_data.pop("total_value")
        validated_data.setdefault("currency", "IQD")
        validated_data["id"] = get_next_id("CN", Contract)
        contract = Contract.objects.create(**validated_data)
        for i, c in enumerate(clauses_data):
            c = dict(c)
            c.pop("id", None)
            c["id"] = get_next_id("CL", ContractClause)
            clause = ContractClause.objects.create(**c)
            ContractClauseLink.objects.create(contract=contract, clause=clause, order=i)
        return contract

    def update(self, instance, validated_data):
        clauses_data = validated_data.pop("clauses", None)
        for k in ("party_a_name", "party_a_title", "party_b_name", "party_b_title", "total_value", "currency"):
            if k in validated_data:
                setattr(instance, k, validated_data.pop(k))
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if clauses_data is not None:
            for link in instance.clause_links.all():
                link.clause.delete()
            instance.clause_links.all().delete()
            for i, c in enumerate(clauses_data):
                c = dict(c)
                c.pop("id", None)
                c["id"] = get_next_id("CL", ContractClause)
                clause = ContractClause.objects.create(**c)
                ContractClauseLink.objects.create(contract=instance, clause=clause, order=i)
        instance.save()
        return instance


# ----- Freelancer -----
class FreelancerSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    role = serializers.ChoiceField(choices=Freelancer.Role.choices)

    class Meta:
        model = Freelancer
        fields = ["id", "name", "phone", "role"]

    def create(self, validated_data):
        validated_data["id"] = get_next_id("FL", Freelancer)
        return super().create(validated_data)


# ----- Freelance Work -----
class FreelanceWorkSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    freelancerId = serializers.PrimaryKeyRelatedField(
        queryset=Freelancer.objects.all(), source="freelancer", write_only=True
    )
    isPaid = serializers.BooleanField(source="is_paid", default=False)
    paymentId = serializers.CharField(source="payment_id", required=False, allow_blank=True)

    class Meta:
        model = FreelanceWork
        fields = ["id", "freelancerId", "description", "date", "price", "currency", "isPaid", "paymentId"]

    def create(self, validated_data):
        validated_data["freelancer"] = validated_data.pop("freelancer")
        validated_data["is_paid"] = validated_data.get("is_paid", False)
        validated_data["payment_id"] = validated_data.get("payment_id", "") or ""
        validated_data["id"] = get_next_id("WK", FreelanceWork)
        return super().create(validated_data)

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["freelancerId"] = str(instance.freelancer_id)
        rep["price"] = str(instance.price)
        rep["isPaid"] = instance.is_paid
        rep["paymentId"] = instance.payment_id or ""
        return rep


# ----- SMS Log -----
class SMSLogSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    timestamp = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", read_only=True)

    class Meta:
        model = SMSLog
        fields = ["id", "to", "body", "status", "timestamp", "error"]

    def create(self, validated_data):
        validated_data["id"] = get_next_id("SL", SMSLog)
        return super().create(validated_data)
