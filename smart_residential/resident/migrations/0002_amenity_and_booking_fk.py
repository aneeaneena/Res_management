from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("resident", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Amenity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("description", models.TextField(blank=True)),
                ("category", models.CharField(choices=[("fitness", "Fitness"), ("leisure", "Leisure"), ("social", "Social")], default="social", max_length=20)),
                ("open_time", models.TimeField()),
                ("close_time", models.TimeField()),
                ("slot_minutes", models.PositiveIntegerField(default=60)),
                ("image_url", models.URLField(blank=True)),
            ],
        ),
        migrations.AddField(
            model_name="amenitybooking",
            name="amenity",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="bookings", to="resident.amenity"),
        ),
        migrations.AddConstraint(
            model_name="amenitybooking",
            constraint=models.UniqueConstraint(fields=("amenity", "start_time"), name="uniq_amenity_slot"),
        ),
    ]
