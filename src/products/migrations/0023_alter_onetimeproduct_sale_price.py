# Generated by Django 5.0.7 on 2024-10-20 13:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0022_onetimeproduct_discount_percentage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='onetimeproduct',
            name='sale_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
    ]
