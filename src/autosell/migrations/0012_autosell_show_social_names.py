# Generated by Django 5.0.12 on 2025-03-15 12:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autosell', '0011_alter_autosellview_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='autosell',
            name='show_social_names',
            field=models.BooleanField(default=True),
        ),
    ]
