# Generated by Django 3.2 on 2023-01-31 16:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lava', '0019_auto_20230124_0954'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'default_permissions': (), 'ordering': ('-date_joined', 'last_name', 'first_name'), 'permissions': (('add_user', 'Can add user'), ('change_user', 'Can change user'), ('delete_user', 'Can delete user'), ('soft_delete_user', 'Can soft delete user'), ('view_user', 'Can view user'), ('list_user', 'Can view users list'), ('restore_user', 'Can restore user'), ('change_current_user', 'Can change user profile'), ('delete_current_user', 'Can delete user profile'), ('soft_delete_current_user', 'Can soft delete user profile')), 'verbose_name': 'user', 'verbose_name_plural': 'users'},
        ),
    ]