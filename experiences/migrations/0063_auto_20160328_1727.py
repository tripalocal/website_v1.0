# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0062_auto_20160324_1508'),
    ]

    operations = [
        migrations.AlterField(
            model_name='provider',
            name='phone_number',
            field=models.CharField(max_length=100, blank=True),
            preserve_default=True,
        ),
    ]
