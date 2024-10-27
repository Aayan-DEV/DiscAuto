# Generated by Django 5.0.7 on 2024-10-13 10:50

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('colddm', '0009_colddm_created_at_alter_colddm_saved_by_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='colddm',
            name='created_at',
        ),
        migrations.AlterField(
            model_name='colddm',
            name='saved_by',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='cold_dms', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='UserColdDMStats',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_cold_dms_posted', models.IntegerField(default=0)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='cold_dm_stats', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Cold DM Stats',
                'verbose_name_plural': 'User Cold DM Stats',
            },
        ),
        migrations.DeleteModel(
            name='DailyColdDMStats',
        ),
    ]
