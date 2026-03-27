from django.db import migrations, models
from secrets import choice


def backfill_water_otps(apps, schema_editor):
    DeliveryItem = apps.get_model("resident", "DeliveryItem")
    water_rows = DeliveryItem.objects.filter(
        label__icontains="water",
        delivery_otp="",
    ).exclude(status="delivered")
    for item in water_rows:
        item.delivery_otp = "".join(choice("0123456789") for _ in range(6))
        item.save(update_fields=["delivery_otp"])


class Migration(migrations.Migration):

    dependencies = [
        ("resident", "0008_deliveryitem_payment_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="deliveryitem",
            name="delivery_otp",
            field=models.CharField(blank=True, max_length=6),
        ),
        migrations.AddField(
            model_name="deliveryitem",
            name="otp_verified_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_water_otps, migrations.RunPython.noop),
    ]
