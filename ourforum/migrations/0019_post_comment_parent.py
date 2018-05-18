# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2018-05-17 22:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ourforum', '0018_auto_20180517_2207'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='comment_parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='childcomment', to='ourforum.Post'),
        ),
    ]