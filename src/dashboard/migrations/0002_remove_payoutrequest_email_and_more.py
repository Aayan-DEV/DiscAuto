# Generated by Django 5.0.7 on 2024-10-26 20:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payoutrequest',
            name='email',
        ),
        migrations.RemoveField(
            model_name='payoutrequest',
            name='username',
        ),
    ]
