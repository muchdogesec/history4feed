# Generated by Django 5.0.6 on 2024-07-22 08:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_alter_feed_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='feed',
            name='retrieve_full_text',
        ),
    ]
