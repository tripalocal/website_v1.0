# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0045_auto_20151216_1002'),
    ]

    operations = [
        migrations.AddField(
            model_name='experience',
            name='fixed_price_max',
            field=models.FloatField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='experience',
            name='fixed_price_min',
            field=models.FloatField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='experience',
            name='price_max',
            field=models.FloatField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='experience',
            name='price_min',
            field=models.FloatField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
