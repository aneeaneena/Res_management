from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("resident", "0003_profile_fields_and_support"),
    ]

    operations = [
        migrations.AddField(
            model_name="maintenancerequest",
            name="location",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="maintenancerequest",
            name="due_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="maintenancerequest",
            name="technician_comments",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="maintenancerequest",
            name="evidence_file",
            field=models.FileField(blank=True, null=True, upload_to="maintenance_evidence/"),
        ),
        migrations.AlterField(
            model_name="maintenancerequest",
            name="status",
            field=models.CharField(choices=[("pending", "Pending"), ("in_progress", "In Progress"), ("completed", "Completed"), ("on_hold", "On Hold")], default="pending", max_length=20),
        ),
    ]
