from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("resident", "0006_notice_publish_and_maintenance_assign"),
    ]

    operations = [
        migrations.AddField(
            model_name="residentprofile",
            name="profile_picture",
            field=models.FileField(blank=True, null=True, upload_to="profile_pics/"),
        ),
    ]
