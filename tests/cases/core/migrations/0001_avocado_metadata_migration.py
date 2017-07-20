# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import migrations, models

class Migration(migrations.Migration):

    def forwards(self, orm):
        "Perform a 'safe' load using Avocado's backup utilities."
        from avocado.core import backup
        backup.safe_load('0001_avocado_metadata', backup_path=None,
            using='default')

    def backwards(self, orm):
        "No backwards migration applicable."
        pass

    operations = [
        migrations.RunPython(forwards, backwards)
    ]
