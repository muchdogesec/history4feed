# Generated by Django 5.0.6 on 2024-09-02 08:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0010_alter_post_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='job',
        ),
        migrations.AlterField(
            model_name='fulltextjob',
            name='post',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='fulltext_jobs', to='app.post'),
        ),
    ]
