# Generated by Django 5.0.7 on 2024-10-13 12:04

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autosell', '0004_autosell_view_count'),
    ]

    operations = [
        migrations.CreateModel(
            name='AutoSellView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('view_date', models.DateField(default=django.utils.timezone.now)),
                ('autosell', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='autosell.autosell')),
            ],
        ),
    ]
