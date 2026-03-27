from django.db import migrations


def backfill_profiles(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    Profile = apps.get_model('accounts', 'Profile')

    for user in User.objects.all():
        if not Profile.objects.filter(user_id=user.id).exists():
            role = 'admin' if user.is_superuser else 'resident'
            Profile.objects.create(user_id=user.id, role=role)


def noop_reverse(apps, schema_editor):
    return


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(backfill_profiles, noop_reverse),
    ]
