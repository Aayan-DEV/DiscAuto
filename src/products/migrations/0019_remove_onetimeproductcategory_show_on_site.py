# Generated by Django 5.0.7 on 2024-10-16 02:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0018_alter_productsale_product_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='onetimeproductcategory',
            name='show_on_site',
        ),
    ]
