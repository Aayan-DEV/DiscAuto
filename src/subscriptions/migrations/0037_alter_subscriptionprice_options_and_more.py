# Generated by Django 5.0.12 on 2025-02-19 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('subscriptions', '0036_alter_subscription_featured_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='subscriptionprice',
            options={'ordering': ['subscription__order', 'order', 'featured', '-updated']},
        ),
        migrations.RemoveField(
            model_name='usersubscription',
            name='subscription_price',
        ),
        migrations.AlterField(
            model_name='subscription',
            name='featured',
            field=models.BooleanField(default=True, help_text='Featured on the pricing page.'),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='groups',
            field=models.ManyToManyField(to='auth.group'),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='order',
            field=models.IntegerField(default=-1, help_text='Ordering on Django pricing page'),
        ),
        migrations.AlterField(
            model_name='subscription',
            name='permissions',
            field=models.ManyToManyField(limit_choices_to={'codename__in': ['pro', 'starter'], 'content_type__app_label': 'subscriptions'}, to='auth.permission'),
        ),
        migrations.AlterField(
            model_name='subscriptionfeature',
            name='title',
            field=models.CharField(help_text='Short title or name of the feature.', max_length=255),
        ),
        migrations.AlterField(
            model_name='subscriptionprice',
            name='featured',
            field=models.BooleanField(default=True, help_text='Featured on the subscription page.'),
        ),
        migrations.AlterField(
            model_name='subscriptionprice',
            name='order',
            field=models.IntegerField(default=-1, help_text='Ordering on Django pricing page'),
        ),
        migrations.AlterField(
            model_name='usersubscription',
            name='status',
            field=models.CharField(blank=True, choices=[('active', 'Active'), ('trailing', 'Trailing'), ('incomplete', 'Incomplete'), ('incomplete_expired', 'Incomplete Expired'), ('past_due', 'Past Due'), ('cancelled', 'Cancelled'), ('unpaid', 'Unpaid'), ('paused', 'Paused')], max_length=20, null=True),
        ),
    ]
