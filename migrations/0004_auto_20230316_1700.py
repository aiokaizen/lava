# Generated by Django 3.2 on 2023-03-16 16:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lava', '0003_auto_20230314_1800'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='backup',
            options={'default_permissions': (), 'ordering': ('-created_at',), 'verbose_name': 'Backup', 'verbose_name_plural': 'Backups'},
        ),
        migrations.AlterModelOptions(
            name='group',
            options={'default_permissions': (), 'ordering': ('name',), 'verbose_name': 'Group', 'verbose_name_plural': 'Groups'},
        ),
        migrations.AlterModelOptions(
            name='permission',
            options={'default_permissions': (), 'ordering': ['content_type__app_label', 'content_type__model', 'codename'], 'permissions': (('set_permission', 'Can set permissions'),), 'verbose_name': 'permission', 'verbose_name_plural': 'permissions'},
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'default_permissions': (), 'ordering': ('-date_joined', 'last_name', 'first_name'), 'permissions': (('change_current_user', 'Can change user profile'), ('delete_current_user', 'Can delete user profile'), ('soft_delete_current_user', 'Can soft delete user profile')), 'verbose_name': 'user', 'verbose_name_plural': 'users'},
        ),
    ]
