# Generated by Django 5.0.7 on 2024-10-27 17:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autosell', '0008_alter_autosell_banner_alter_autosell_profile_picture'),
    ]

    operations = [
        migrations.AlterField(
            model_name='autosell',
            name='name',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='autosell',
            name='title',
            field=models.CharField(max_length=200),
        ),
    ]
