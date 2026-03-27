from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_alter_profile_role"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="phone",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name="profile",
            name="profile_picture",
            field=models.FileField(blank=True, null=True, upload_to="profile_pics/"),
        ),
    ]
