from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("resident", "0004_maintenance_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="deliveryitem",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("ready", "Ready"),
                    ("picked_up", "Picked Up"),
                    ("delivered", "Delivered"),
                    ("skipped", "Skipped"),
                ],
                default="pending",
                max_length=20,
            ),
        ),
    ]
