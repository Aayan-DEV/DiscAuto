# Generated by Django 5.0.7 on 2024-10-13 12:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('autosell', '0005_autosellview'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='autosell',
            name='view_count',
        ),
    ]
