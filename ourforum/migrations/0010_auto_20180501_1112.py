# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2018-05-01 03:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ourforum', '0009_auto_20180430_2029'),
    ]

    operations = [
        migrations.RenameField(
            model_name='application',
            old_name='created_at',
            new_name='created_on',
        ),
        migrations.RemoveField(
            model_name='application',
            name='updated_at',
        ),
        migrations.AddField(
            model_name='application',
            name='updated_on',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
