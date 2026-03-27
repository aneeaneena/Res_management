from django.db import migrations, models
from secrets import choice


def backfill_maintenance_otps(apps, schema_editor):
    MaintenanceRequest = apps.get_model("resident", "MaintenanceRequest")
    rows = MaintenanceRequest.objects.filter(completion_otp="")
    for item in rows:
        item.completion_otp = "".join(choice("0123456789") for _ in range(6))
        item.save(update_fields=["completion_otp"])


class Migration(migrations.Migration):

    dependencies = [
        ("resident", "0009_deliveryitem_otp_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="maintenancerequest",
            name="completion_otp",
            field=models.CharField(blank=True, max_length=6),
        ),
        migrations.AddField(
            model_name="maintenancerequest",
            name="otp_verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_maintenance_otps, migrations.RunPython.noop),
    ]
