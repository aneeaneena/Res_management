from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0002_backfill_profiles'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='delivery_type',
            field=models.CharField(blank=True, choices=[('milk', 'Milk'), ('water', 'Water')], max_length=10, null=True),
        ),
    ]
