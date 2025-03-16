# Generated by Django 5.0.12 on 2025-03-15 16:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autosell', '0016_alter_landingpage_name'),
        ('products', '0045_unlimitedproduct_landing_page'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unlimitedproduct',
            name='landing_pages',
            field=models.ManyToManyField(blank=True, related_name='unlimited_products', to='autosell.autosell'),
        ),
    ]
