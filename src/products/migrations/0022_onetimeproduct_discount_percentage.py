# Generated by Django 5.0.7 on 2024-10-20 12:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0021_onetimeproduct_sale_price_delete_productitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='onetimeproduct',
            name='discount_percentage',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
    ]
