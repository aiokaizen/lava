# Generated by Django 3.2 on 2023-01-23 17:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lava', '0016_alter_user_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='logentry',
            options={'default_permissions': (), 'ordering': ['-action_time'], 'permissions': (('list_log_entry', 'Can view log entry journal'), ('export_log_entry', 'Can export log entry journal')), 'verbose_name': 'Log entry', 'verbose_name_plural': 'Log entries'},
        ),
    ]