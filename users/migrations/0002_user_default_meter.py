# Generated by Django 3.0.8 on 2020-08-27 10:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('smart_meter', '0002_auto_20200827_1013'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='default_meter',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='default',
                                    to='smart_meter.SmartMeter'),
        ),
    ]
