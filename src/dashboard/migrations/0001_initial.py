# Generated by Django 5.0.7 on 2024-10-26 17:31

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PayoutRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(max_length=10)),
                ('payment_method', models.CharField(choices=[('paypal_email', 'PayPal'), ('btc_wallet', 'Bitcoin'), ('ltc_wallet', 'Litecoin'), ('sol_wallet', 'Solana'), ('eth_wallet', 'Ethereum'), ('usdt_bep20_wallet', 'USDT BEP20'), ('usdt_erc20_wallet', 'USDT ERC20'), ('usdt_prc20_wallet', 'USDT PRC20'), ('usdt_sol_wallet', 'USDT SOL'), ('usdt_trc20_wallet', 'USDT TRC20')], max_length=255)),
                ('contact_method', models.CharField(max_length=50)),
                ('contact_info', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
