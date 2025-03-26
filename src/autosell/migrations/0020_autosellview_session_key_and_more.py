# Generated by Django 5.0.12 on 2025-03-26 05:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autosell', '0019_alter_landingpage_one_time_products'),
    ]

    operations = [
        migrations.AddField(
            model_name='autosellview',
            name='session_key',
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
        migrations.AlterField(
            model_name='autosellview',
            name='auto_sell',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='views', to='autosell.autosell'),
        ),
        migrations.AlterField(
            model_name='autosellview',
            name='ip_address',
            field=models.GenericIPAddressField(),
        ),
        migrations.AlterUniqueTogether(
            name='autosellview',
            unique_together={('auto_sell', 'session_key')},
        ),
    ]
