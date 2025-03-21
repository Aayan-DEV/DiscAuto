# Generated by Django 5.0.12 on 2025-03-19 05:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_rename_contact_info_payoutrequest_payout_address_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payoutrequest',
            name='currency',
            field=models.CharField(choices=[('EUR', 'EUR'), ('USD', 'USD'), ('GBP', 'GBP'), ('BTC', 'BTC'), ('LTC', 'LTC'), ('SOL', 'SOL'), ('ETH', 'ETH'), ('USDT.BEP20', 'USDT (BEP20)'), ('USDT.ERC20', 'USDT (ERC20)'), ('USDT.PRC20', 'USDT (PRC20)'), ('USDT.TRC20', 'USDT (TRC20)'), ('USDT.SOL', 'USDT (SOL)')], default='EUR', max_length=10),
        ),
    ]
