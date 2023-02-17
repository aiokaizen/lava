# Generated by Django 3.2 on 2023-02-13 16:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lava', '0022_auto_20230210_1515'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='backup',
            options={'default_permissions': (), 'ordering': ('-created_at',), 'permissions': (('add_backup', 'Can add backup'), ('delete_backup', 'Can delete backup'), ('soft_delete_backup', 'Can soft backup'), ('list_backup', 'Can view backup')), 'verbose_name': 'Backup', 'verbose_name_plural': 'Backups'},
        ),
    ]