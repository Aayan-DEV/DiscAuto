# Generated by Django 5.0.7 on 2024-10-20 14:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0024_alter_onetimeproduct_discount_percentage'),
    ]

    operations = [
        migrations.AddField(
            model_name='unlimitedproduct',
            name='sale_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
