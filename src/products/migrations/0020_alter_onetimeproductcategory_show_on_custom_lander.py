# Generated by Django 5.0.7 on 2024-10-16 02:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0019_remove_onetimeproductcategory_show_on_site'),
    ]

    operations = [
        migrations.AlterField(
            model_name='onetimeproductcategory',
            name='show_on_custom_lander',
            field=models.BooleanField(default=True),
        ),
    ]