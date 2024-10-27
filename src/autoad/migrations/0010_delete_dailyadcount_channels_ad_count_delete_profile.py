# Generated by Django 5.0.7 on 2024-10-13 09:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autoad', '0009_dailyadcount_profile'),
    ]

    operations = [
        migrations.DeleteModel(
            name='DailyAdCount',
        ),
        migrations.AddField(
            model_name='channels',
            name='ad_count',
            field=models.IntegerField(default=0),
        ),
        migrations.DeleteModel(
            name='Profile',
        ),
    ]
