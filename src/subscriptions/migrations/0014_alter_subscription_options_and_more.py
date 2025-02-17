# Generated by Django 5.0.7 on 2024-07-29 04:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0013_alter_subscriptionprice_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='subscription',
            options={'ordering': ['order', 'featured', '-updated'], 'permissions': [('pro', 'Pro Perm'), ('starter', 'Starter Perm')]},
        ),
        migrations.AlterField(
            model_name='subscription',
            name='featured',
            field=models.BooleanField(default=True, help_text='Featured on the pricing page.'),
        ),
    ]
