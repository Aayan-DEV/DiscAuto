# Generated by Django 5.0.7 on 2024-10-01 14:41

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('colddm', '0002_delete_colddmsave'),
    ]

    operations = [
        migrations.CreateModel(
            name='ColdDM',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=150)),
                ('user_id', models.CharField(max_length=150)),
                ('note', models.TextField(blank=True, null=True)),
            ],
        ),
    ]
