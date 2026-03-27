from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("resident", "0002_amenity_and_booking_fk"),
    ]

    operations = [
        migrations.AddField(
            model_name="residentprofile",
            name="phone",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name="residentprofile",
            name="emergency_name",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="residentprofile",
            name="emergency_phone",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name="residentprofile",
            name="lease_file",
            field=models.FileField(blank=True, null=True, upload_to="leases/"),
        ),
        migrations.CreateModel(
            name="SupportMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("subject", models.CharField(max_length=200)),
                ("message", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("resident", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="support_messages", to="auth.user")),
            ],
        ),
    ]
