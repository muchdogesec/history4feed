# Generated by Django 5.0.9 on 2024-11-28 12:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0017_feed_pretty_url_alter_feed_feed_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='job',
            name='profile_id',
        ),
    ]