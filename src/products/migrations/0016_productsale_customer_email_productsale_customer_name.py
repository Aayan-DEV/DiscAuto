# Generated by Django 5.0.7 on 2024-10-13 13:43

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0015_productsale_unlimited_product_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='productsale',
            name='customer_email',
            field=models.EmailField(default=django.utils.timezone.now, max_length=254),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='productsale',
            name='customer_name',
            field=models.CharField(default=django.utils.timezone.now, max_length=255),
            preserve_default=False,
        ),
    ]
