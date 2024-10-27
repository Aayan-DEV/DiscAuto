# Generated by Django 5.0.7 on 2024-10-21 11:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0028_unlimitedproduct_btc_price_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='onetimeproduct',
            name='btc_price',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='onetimeproduct',
            name='eth_price',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='onetimeproduct',
            name='ltc_price',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='onetimeproduct',
            name='usdt_price',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]