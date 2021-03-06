# Generated by Django 3.0.8 on 2020-09-22 12:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('smart_meter', '0004_auto_20200921_0926'),
    ]

    operations = [
        migrations.AddField(
            model_name='smartmeter',
            name='solar_timestamp',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='smartmeter',
            name='gpx_version',
            field=models.CharField(default='undefined', max_length=20),
        ),
        migrations.AlterField(
            model_name='smartmeter',
            name='sn_gas',
            field=models.CharField(blank=True, default='', max_length=40, unique=True),
        ),
    ]
