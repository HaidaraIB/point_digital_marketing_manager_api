# Migration for Point Digital Marketing Manager v4 frontend

import uuid
from django.db import migrations, models


def voucher_expenditure_to_payment(apps, schema_editor):
    Voucher = apps.get_model("api", "Voucher")
    Voucher.objects.filter(type="EXPENDITURE").update(type="PAYMENT")


def contract_status_to_v4(apps, schema_editor):
    Contract = apps.get_model("api", "Contract")
    Contract.objects.filter(status="EXPIRED").update(status="ARCHIVED")
    Contract.objects.filter(status="DRAFT").update(status="ACTIVE")


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0002_alter_agencysettings_logo"),
    ]

    operations = [
        # Quotation
        migrations.AddField(
            model_name="quotation",
            name="client_phone",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="quotation",
            name="currency",
            field=models.CharField(default="IQD", max_length=3),
        ),
        # QuotationItem
        migrations.AddField(
            model_name="quotationitem",
            name="currency",
            field=models.CharField(blank=True, default="", max_length=3),
        ),
        # AgencySettings
        migrations.AddField(
            model_name="agencysettings",
            name="twilio",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="agencysettings",
            name="exchange_rate",
            field=models.DecimalField(decimal_places=2, default=1500, max_digits=14),
        ),
        # Voucher: add new fields then data migrate then alter type choices
        migrations.AddField(
            model_name="voucher",
            name="currency",
            field=models.CharField(default="IQD", max_length=3),
        ),
        migrations.AddField(
            model_name="voucher",
            name="party_phone",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name="voucher",
            name="category",
            field=models.CharField(
                blank=True,
                choices=[
                    ("SALARY", "راتب"),
                    ("DAILY", "يومي"),
                    ("GENERAL", "عام"),
                    ("VOUCHER", "وصل"),
                ],
                max_length=20,
            ),
        ),
        migrations.RunPython(voucher_expenditure_to_payment, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="voucher",
            name="type",
            field=models.CharField(
                choices=[("RECEIPT", "قبض"), ("PAYMENT", "صرف")],
                max_length=20,
            ),
        ),
        # Contract: add currency, then data migrate status, then alter status choices
        migrations.AddField(
            model_name="contract",
            name="currency",
            field=models.CharField(default="IQD", max_length=3),
        ),
        migrations.RunPython(contract_status_to_v4, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="contract",
            name="status",
            field=models.CharField(
                choices=[("ACTIVE", "Active"), ("ARCHIVED", "Archived")],
                default="ACTIVE",
                max_length=20,
            ),
        ),
        # SMSLog
        migrations.CreateModel(
            name="SMSLog",
            fields=[
                ("id", models.CharField(default=uuid.uuid4, editable=False, max_length=36, primary_key=True, serialize=False)),
                ("to", models.CharField(max_length=50)),
                ("body", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[("SUCCESS", "Success"), ("FAILED", "Failed")],
                        max_length=20,
                    ),
                ),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("error", models.TextField(blank=True)),
            ],
            options={
                "db_table": "api_sms_log",
                "ordering": ["-timestamp"],
            },
        ),
    ]
