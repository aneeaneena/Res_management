from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("resident", "0007_residentprofile_profile_picture"),
    ]

    operations = [
        migrations.AddField(
            model_name="deliveryitem",
            name="payment_amount",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
        ),
        migrations.AddField(
            model_name="deliveryitem",
            name="payment_method",
            field=models.CharField(
                choices=[("na", "N/A"), ("online", "Online"), ("at_delivery", "Pay at Delivery")],
                default="na",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="deliveryitem",
            name="payment_reference",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="deliveryitem",
            name="payment_status",
            field=models.CharField(
                choices=[("na", "N/A"), ("pending", "Pending"), ("paid", "Paid")],
                default="na",
                max_length=20,
            ),
        ),
    ]
