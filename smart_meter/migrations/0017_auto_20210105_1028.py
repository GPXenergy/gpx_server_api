# Generated by Django 3.0.8 on 2021-01-05 09:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smart_meter', '0016_smartmeter_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='smartmeter',
            name='sn_gas',
            field=models.CharField(max_length=40, null=True),
        ),
        migrations.AlterField(
            model_name='smartmeter',
            name='sn_power',
            field=models.CharField(max_length=40),
        ),
    ]
