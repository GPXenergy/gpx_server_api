# Generated by Django 3.0.8 on 2020-09-23 11:25

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('smart_meter', '0008_remove_gasmeasurement_duration'),
    ]

    operations = [
        migrations.AddField(
            model_name='smartmeter',
            name='last_update',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
