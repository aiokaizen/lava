# Generated by Django 3.2 on 2023-06-05 14:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lava', '0012_bank_routing_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankaccount',
            name='balance',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=14, verbose_name='Balance'),
        ),
    ]