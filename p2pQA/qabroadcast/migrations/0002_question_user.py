# Generated by Django 2.2.2 on 2019-07-01 19:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('qabroadcast', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='question',
            name='user',
            field=models.CharField(default='', max_length=128),
        ),
    ]
