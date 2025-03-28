# Generated by Django 5.0.7 on 2024-10-13 13:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0016_productsale_customer_email_productsale_customer_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productsale',
            name='product',
            field=models.ForeignKey(blank=True, default='', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sales', to='products.onetimeproduct'),
        ),
        migrations.AlterField(
            model_name='productsale',
            name='unlimited_product',
            field=models.ForeignKey(blank=True, default='', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sales', to='products.unlimitedproduct'),
        ),
    ]
