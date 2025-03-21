# Generated by Django 5.0.12 on 2025-03-19 05:07

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0070_remove_productsale_conversion_fee_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userincome',
            name='btc_total',
        ),
        migrations.RemoveField(
            model_name='userincome',
            name='eth_total',
        ),
        migrations.RemoveField(
            model_name='userincome',
            name='eur_total',
        ),
        migrations.RemoveField(
            model_name='userincome',
            name='gbp_total',
        ),
        migrations.RemoveField(
            model_name='userincome',
            name='ltc_total',
        ),
        migrations.RemoveField(
            model_name='userincome',
            name='ltct_total',
        ),
        migrations.RemoveField(
            model_name='userincome',
            name='sol_total',
        ),
        migrations.RemoveField(
            model_name='userincome',
            name='usd_total',
        ),
        migrations.RemoveField(
            model_name='userincome',
            name='usdt_bep20_total',
        ),
        migrations.RemoveField(
            model_name='userincome',
            name='usdt_erc20_total',
        ),
        migrations.RemoveField(
            model_name='userincome',
            name='usdt_prc20_total',
        ),
        migrations.RemoveField(
            model_name='userincome',
            name='usdt_sol_total',
        ),
        migrations.RemoveField(
            model_name='userincome',
            name='usdt_trc20_total',
        ),
        migrations.AddField(
            model_name='userincome',
            name='BTC_TOTAL',
            field=models.DecimalField(decimal_places=8, default=Decimal('0E-8'), max_digits=10),
        ),
        migrations.AddField(
            model_name='userincome',
            name='ETH_TOTAL',
            field=models.DecimalField(decimal_places=8, default=Decimal('0E-8'), max_digits=10),
        ),
        migrations.AddField(
            model_name='userincome',
            name='EUR_TOTAL',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
        migrations.AddField(
            model_name='userincome',
            name='LTC_TOTAL',
            field=models.DecimalField(decimal_places=8, default=Decimal('0E-8'), max_digits=10),
        ),
        migrations.AddField(
            model_name='userincome',
            name='LTCT_TOTAL',
            field=models.DecimalField(decimal_places=8, default=Decimal('0E-8'), max_digits=10),
        ),
        migrations.AddField(
            model_name='userincome',
            name='SOL_TOTAL',
            field=models.DecimalField(decimal_places=8, default=Decimal('0E-8'), max_digits=10),
        ),
        migrations.AddField(
            model_name='userincome',
            name='USDT_BEP20_TOTAL',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
        migrations.AddField(
            model_name='userincome',
            name='USDT_ERC20_TOTAL',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
        migrations.AddField(
            model_name='userincome',
            name='USDT_PRC20_TOTAL',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
        migrations.AddField(
            model_name='userincome',
            name='USDT_SOL_TOTAL',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
        migrations.AddField(
            model_name='userincome',
            name='USDT_TRC20_TOTAL',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10),
        ),
    ]
