# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2018-05-10 09:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ourforum', '0014_auto_20180510_1656'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ourforumuserprofile',
            name='birthday',
            field=models.DateTimeField(blank=True, null=True, verbose_name='生日'),
        ),
    ]
