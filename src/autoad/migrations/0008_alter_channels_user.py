# Generated by Django 5.0.7 on 2024-10-01 13:14

import autoad.models
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autoad', '0007_channels_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='channels',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='autoad_channels', to=settings.AUTH_USER_MODEL),
        ),
    ]
