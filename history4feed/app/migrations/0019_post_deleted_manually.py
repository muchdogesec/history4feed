# Generated by Django 5.0.9 on 2024-11-29 15:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0018_remove_job_profile_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='deleted_manually',
            field=models.BooleanField(default=False, help_text='this post is hidden from user'),
        ),
    ]
