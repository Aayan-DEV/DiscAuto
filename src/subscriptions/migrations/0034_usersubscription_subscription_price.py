# Generated by Django 5.0.12 on 2025-02-19 14:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0033_alter_subscriptionfeature_icon'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersubscription',
            name='subscription_price',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='subscriptions.subscriptionprice'),
        ),
    ]
