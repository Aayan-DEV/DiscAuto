# Generated by Django 5.0.12 on 2025-02-18 00:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0024_usersubscription_price'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usersubscription',
            name='price',
        ),
    ]
