# Generated by Django 3.2 on 2023-01-23 14:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lava', '0015_logentry'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='user',
            options={'default_permissions': (), 'ordering': ('-date_joined', 'last_name', 'first_name'), 'permissions': (('add_user', 'Can add user'), ('change_user', 'Can change user'), ('delete_user', 'Can delete user'), ('soft_delete_user', 'Can soft delete user'), ('view_user', 'Can view user'), ('list_user', 'Can view users list'), ('restore_user', 'Can restore user')), 'verbose_name': 'user', 'verbose_name_plural': 'users'},
        ),
    ]