# Generated by Django 5.0.7 on 2024-10-06 16:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0012_onetimeproduct_stripe_price_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='productsale',
            name='unlimited_product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sales', to='products.unlimitedproduct'),
        ),
        migrations.AlterField(
            model_name='onetimeproduct',
            name='description',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='productsale',
            name='product',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sales', to='products.onetimeproduct'),
        ),
    ]