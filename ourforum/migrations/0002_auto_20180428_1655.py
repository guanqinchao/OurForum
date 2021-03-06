# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2018-04-28 08:55
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ourforum', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='application',
            options={'verbose_name_plural': 'Applications'},
        ),
        migrations.AlterModelOptions(
            name='loginuser',
            options={'ordering': ['-date_joined'], 'verbose_name_plural': 'User'},
        ),
        migrations.AlterModelOptions(
            name='message',
            options={'verbose_name_plural': 'Messages'},
        ),
        migrations.AlterModelOptions(
            name='notice',
            options={'ordering': ['-created_at'], 'verbose_name_plural': 'Notices'},
        ),
        migrations.AlterModelOptions(
            name='ourforumuserprofile',
            options={'verbose_name': 'UserProfile', 'verbose_name_plural': 'UserProfiles'},
        ),
    ]
