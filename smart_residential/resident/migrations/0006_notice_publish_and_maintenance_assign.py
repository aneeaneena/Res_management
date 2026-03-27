from django.db import migrations, models
import django.db.models.deletion
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ("resident", "0005_deliveryitem_skipped"),
    ]

    operations = [
        migrations.AddField(
            model_name="maintenancerequest",
            name="assigned_to",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="assigned_maintenance_requests",
                to="auth.user",
            ),
        ),
        migrations.AddField(
            model_name="maintenancerequest",
            name="priority",
            field=models.CharField(
                choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")],
                default="medium",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="residentnotice",
            name="publish_from",
            field=models.DateTimeField(default=timezone.now),
        ),
        migrations.AddField(
            model_name="residentnotice",
            name="publish_until",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
