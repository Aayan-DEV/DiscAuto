# Generated by Django 5.0.7 on 2024-10-26 19:00

import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0036_userprofile_delete_userincome'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserIncome',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usd_total', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=15)),
                ('gbp_total', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=15)),
                ('eur_total', models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=15)),
                ('btc_total', models.DecimalField(decimal_places=8, default=Decimal('0E-8'), max_digits=30)),
                ('ltc_total', models.DecimalField(decimal_places=8, default=Decimal('0E-8'), max_digits=30)),
                ('sol_total', models.DecimalField(decimal_places=8, default=Decimal('0E-8'), max_digits=30)),
                ('eth_total', models.DecimalField(decimal_places=8, default=Decimal('0E-8'), max_digits=30)),
                ('usdt_bep20_total', models.DecimalField(decimal_places=8, default=Decimal('0E-8'), max_digits=30)),
                ('usdt_erc20_total', models.DecimalField(decimal_places=8, default=Decimal('0E-8'), max_digits=30)),
                ('usdt_prc20_total', models.DecimalField(decimal_places=8, default=Decimal('0E-8'), max_digits=30)),
                ('usdt_sol_total', models.DecimalField(decimal_places=8, default=Decimal('0E-8'), max_digits=30)),
                ('usdt_trc20_total', models.DecimalField(decimal_places=8, default=Decimal('0E-8'), max_digits=30)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='income', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.DeleteModel(
            name='UserProfile',
        ),
    ]
