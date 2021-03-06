# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-01-07 10:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Thread',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uid', models.IntegerField()),
                ('time', models.DateTimeField()),
                ('title', models.TextField()),
                ('content', models.TextField()),
                ('tag', models.CharField(default='', max_length=50)),
                ('reply', models.IntegerField(default=0)),
            ],
        ),
    ]
