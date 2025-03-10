# Generated by Django 5.0.7 on 2024-07-29 14:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0020_usersubscription_current_period_end_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersubscription',
            name='status',
            field=models.CharField(blank=True, choices=[('active', 'Active'), ('trailing', 'Trailing'), ('incomplete', 'Incomplete'), ('incomplete_expired', 'Incomplete Expired'), ('past_due', 'Past Due'), ('cancelled', 'Cancelled'), ('unpaid', 'Unpaid'), ('paused', 'Paused')], max_length=20, null=True),
        ),
    ]
