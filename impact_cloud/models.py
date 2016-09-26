# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.db import models


class Experimenttable(models.Model):
    experiment_id = models.IntegerField(primary_key=True, blank=True, null=True)
    import_date = models.TextField(blank=True, null=True)
    experiment_title = models.TextField(blank=True, null=True)
    experiment_start_date = models.TextField(blank=True, null=True)
    experiment_end_date = models.TextField(blank=True, null=True)
    primary_scientist_name = models.TextField(blank=True, null=True)
    secondary_scientist_name = models.TextField(blank=True, null=True)
    medium_base = models.TextField(blank=True, null=True)
    medium_supplements = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'experimentTable'