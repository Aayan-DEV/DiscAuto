# Generated by Django 5.0.7 on 2024-09-16 07:58

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autoad', '0003_channels_hours_channels_minutes_channels_seconds'),
    ]

    operations = [
        migrations.AddField(
            model_name='channels',
            name='start_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]