# Generated by Django 3.2 on 2023-09-12 14:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lava', '0017_auto_20230807_1109'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='is_system',
            field=models.BooleanField(default=False, verbose_name='Is system group'),
        ),
    ]