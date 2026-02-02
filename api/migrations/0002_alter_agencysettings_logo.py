# Generated migration: allow logo as URL or base64 data URL

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="agencysettings",
            name="logo",
            field=models.TextField(blank=True),
        ),
    ]
