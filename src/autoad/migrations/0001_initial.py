# Generated by Django 5.0.7 on 2024-08-08 18:08

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AutoAdConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('universal_message', models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='AutoAdDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel_id', models.BigIntegerField()),
                ('usernames', models.CharField(max_length=255)),
                ('slowmode_duration', models.IntegerField()),
                ('channel_name', models.CharField(max_length=255)),
                ('server_name', models.CharField(max_length=255)),
                ('universal_message', models.TextField(blank=True)),
                ('custom_message', models.TextField(blank=True)),
                ('bot_running', models.BooleanField(default=False)),
                ('token', models.CharField(max_length=255)),
                ('box_number', models.IntegerField()),
                ('config', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='details', to='autoad.autoadconfig')),
            ],
        ),
        migrations.CreateModel(
            name='AutoAdUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=255)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='autoadconfig',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='configs', to='autoad.autoaduser'),
        ),
    ]
