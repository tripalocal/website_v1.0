# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0051_auto_20160107_1703'),
    ]

    operations = [
        migrations.AddField(
            model_name='customitinerary',
            name='cities',
            field=models.TextField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
