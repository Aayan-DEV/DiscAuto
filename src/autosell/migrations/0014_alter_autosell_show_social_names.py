# Generated by Django 5.0.12 on 2025-03-15 12:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autosell', '0013_alter_autosellview_auto_sell'),
    ]

    operations = [
        migrations.AlterField(
            model_name='autosell',
            name='show_social_names',
            field=models.BooleanField(default=False),
        ),
    ]
