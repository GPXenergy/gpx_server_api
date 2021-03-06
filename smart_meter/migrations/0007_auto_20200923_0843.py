# Generated by Django 3.0.8 on 2020-09-23 08:43

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('smart_meter', '0006_auto_20200922_1258'),
    ]

    operations = [
        migrations.RenameField(
            model_name='gasmeasurement',
            old_name='gas_import',
            new_name='gas',
        ),
        migrations.RenameField(
            model_name='powermeasurement',
            old_name='power_export',
            new_name='power_exp',
        ),
        migrations.RenameField(
            model_name='powermeasurement',
            old_name='power_import',
            new_name='power_imp',
        ),
        migrations.RenameField(
            model_name='solarmeasurement',
            old_name='solar_export',
            new_name='solar',
        ),
    ]
