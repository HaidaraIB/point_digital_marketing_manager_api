# Migration: store exchange rate at creation so changing settings only affects new operations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0006_freelance_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="quotation",
            name="exchange_rate",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="سعر الصرف عند الإصدار (للعرض فقط، لا يُعدّل لاحقاً)",
                max_digits=14,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="voucher",
            name="exchange_rate",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="سعر الصرف عند الإصدار (للعرض فقط، لا يُعدّل لاحقاً)",
                max_digits=14,
                null=True,
            ),
        ),
    ]
