# Generated by Django 5.0.7 on 2024-07-29 06:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0014_alter_subscription_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriptionprice',
            name='features',
            field=models.TextField(blank=True, help_text='Features for pricing, seperated by new line', null=True),
        ),
        migrations.AlterField(
            model_name='subscriptionprice',
            name='subscription',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='subscriptions.subscription'),
        ),
    ]
