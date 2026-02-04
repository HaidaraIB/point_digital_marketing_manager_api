# Generated manually for freelance feature

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0005_alter_voucher_category"),
    ]

    operations = [
        migrations.AlterField(
            model_name="voucher",
            name="category",
            field=models.CharField(
                blank=True,
                choices=[
                    ("SALARY", "راتب"),
                    ("DAILY", "يومي"),
                    ("GENERAL", "عام"),
                    ("VOUCHER", "وصل"),
                    ("OWNER_WITHDRAWAL", "سحب مالك"),
                    ("FREELANCE", "فري لانس"),
                ],
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="Freelancer",
            fields=[
                ("id", models.CharField(editable=False, max_length=36, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=255)),
                ("phone", models.CharField(max_length=50)),
                (
                    "role",
                    models.CharField(
                        choices=[("PHOTOGRAPHER", "مصور"), ("EDITOR", "مونتير")],
                        default="PHOTOGRAPHER",
                        max_length=20,
                    ),
                ),
            ],
            options={
                "db_table": "api_freelancer",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="FreelanceWork",
            fields=[
                ("id", models.CharField(editable=False, max_length=36, primary_key=True, serialize=False)),
                ("description", models.TextField()),
                ("date", models.CharField(max_length=50)),
                ("price", models.DecimalField(decimal_places=2, max_digits=14)),
                ("currency", models.CharField(default="IQD", max_length=3)),
                ("is_paid", models.BooleanField(default=False)),
                ("payment_id", models.CharField(blank=True, max_length=36)),
                (
                    "freelancer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="works",
                        to="api.freelancer",
                    ),
                ),
            ],
            options={
                "db_table": "api_freelance_work",
                "ordering": ["-date", "id"],
            },
        ),
    ]
