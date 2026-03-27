from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_profile_phone_profile_picture"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="application_document",
            field=models.FileField(blank=True, null=True, upload_to="application_docs/"),
        ),
    ]
