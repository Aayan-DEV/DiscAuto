# Generated by Django 5.0.7 on 2024-10-20 14:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0025_unlimitedproduct_sale_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='unlimitedproduct',
            name='discount_percentage',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
