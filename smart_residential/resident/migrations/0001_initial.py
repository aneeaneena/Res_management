from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ResidentProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("unit", models.CharField(blank=True, max_length=20)),
                ("building", models.CharField(blank=True, max_length=100)),
                ("avatar_url", models.URLField(blank=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="resident_profile", to="auth.user")),
            ],
        ),
        migrations.CreateModel(
            name="ResidentNotice",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("body", models.TextField()),
                ("priority", models.CharField(choices=[("normal", "Normal"), ("important", "Important"), ("urgent", "Urgent")], default="normal", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="MaintenanceRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("in_progress", "In Progress"), ("completed", "Completed")], default="pending", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("resident", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="maintenance_requests", to="auth.user")),
            ],
        ),
        migrations.CreateModel(
            name="AmenityBooking",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amenity_name", models.CharField(max_length=120)),
                ("status", models.CharField(choices=[("booked", "Booked"), ("completed", "Completed"), ("cancelled", "Cancelled")], default="booked", max_length=20)),
                ("start_time", models.DateTimeField()),
                ("end_time", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("resident", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="amenity_bookings", to="auth.user")),
            ],
        ),
        migrations.CreateModel(
            name="DeliveryItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("carrier", models.CharField(max_length=60)),
                ("label", models.CharField(max_length=120)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("ready", "Ready"), ("picked_up", "Picked Up"), ("delivered", "Delivered")], default="pending", max_length=20)),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("resident", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="delivery_items", to="auth.user")),
            ],
        ),
    ]
