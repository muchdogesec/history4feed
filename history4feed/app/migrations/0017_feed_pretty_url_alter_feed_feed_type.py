# Generated by Django 5.0.9 on 2024-11-27 06:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0016_alter_post_author'),
    ]

    operations = [
        migrations.AddField(
            model_name='feed',
            name='pretty_url',
            field=models.URLField(default=None, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='feed',
            name='feed_type',
            field=models.CharField(choices=[('rss', 'Rss'), ('atom', 'Atom'), ('skeleton', 'Skeleton')], editable=False, help_text='type of feed', max_length=12),
        ),
    ]
