# from django.db import models

# Create your models here.
# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.

from __future__ import unicode_literals

from django.db import models
# from impact.TrialIdentifier import TrialIdentifier
# from impact.AnalyteData import TimeCourse
# from impact.SingleTrial import SingleTrial
#
#
# class Project(models.Model):
#     project_name = models.TextField()
#     project_start_date = models.DateField()
#     project_end_date = models.DateField(blank=True)
#
# class Experiment(models.Model):
#     _DATABASE ='impact'
#     experiment_id = models.IntegerField(primary_key=True, blank=True, null=False)
#     import_date = models.TextField(blank=True, null=True)
#     experiment_title = models.TextField(blank=True, null=True)
#     experiment_start_date = models.TextField(blank=True, null=True)
#     experiment_end_date = models.TextField(blank=True, null=True)
#     primary_scientist_name = models.TextField(blank=True, null=True)
#     secondary_scientist_name = models.TextField(blank=True, null=True)
#     medium_base = models.TextField(blank=True, null=True)
#     medium_supplements = models.TextField(blank=True, null=True)
#     notes = models.TextField(blank=True, null=True)
#
#     class Meta:
#         managed = True
#         db_table = 'experimentTable'
#
#
# class Replicate(models.Model):
#     _DATABASE ='impact'
#
#     replicate_id = models.IntegerField(db_column='replicateID', primary_key=True, blank=True, null=False)  # Field name made lowercase.
#     experiment = models.ForeignKey(Experiment, models.DO_NOTHING, blank=True, null=True)
#     strain_id = models.TextField(blank=True, null=True)
#     id_1 = models.TextField(blank=True, null=True)
#     id_2 = models.TextField(blank=True, null=True)
#     id_3 = models.TextField(blank=True, null=True)
#
#     class Meta:
#         db_table = 'replicateTable'
#
#
# class Singletrial(models.Model):
#     _DATABASE ='impact'
#
#     singletrialid = models.IntegerField(db_column='singleTrialID', primary_key=True, blank=True, null=False)  # Field name made lowercase.
#     replicateid = models.ForeignKey(Replicate, models.DO_NOTHING, db_column='replicateID', blank=True, null=True)  # Field name made lowercase.
#     replicate_id = models.IntegerField(blank=True, null=True)
#     yieldsdict = models.BinaryField(db_column='yieldsDict', blank=True, null=True)  # Field name made lowercase.
#
#     class Meta:
#         managed = True
#         db_table = 'singleTrialTable'
#
#
# class SingletrialtableAvg(models.Model):
#     _DATABASE ='impact'
#
#     singletrialid_avg = models.IntegerField(db_column='singleTrialID_avg', primary_key=True, blank=True, null=False)  # Field name made lowercase.
#     replicateid = models.ForeignKey(Replicate, models.DO_NOTHING, db_column='replicateID', blank=True, null=True)  # Field name made lowercase.
#     replicate_id = models.IntegerField(blank=True, null=True)
#     yieldsdict = models.BinaryField(db_column='yieldsDict', blank=True, null=True)  # Field name made lowercase.
#
#     class Meta:
#         managed = True
#         db_table = 'singleTrialTable_avg'
#
#
# class SingletrialtableStd(models.Model):
#     _DATABASE ='impact'
#
#     singletrialid_std = models.IntegerField(db_column='singleTrialID_std', primary_key=True, blank=True, null=False)  # Field name made lowercase.
#     replicateid = models.ForeignKey(Replicate, models.DO_NOTHING, db_column='replicateID', blank=True, null=True)  # Field name made lowercase.
#     replicate_id = models.IntegerField(blank=True, null=True)
#     yieldsdict = models.BinaryField(db_column='yieldsDict', blank=True, null=True)  # Field name made lowercase.
#
#     class Meta:
#         managed = True
#         db_table = 'singleTrialTable_std'
#
#
# class Timecoursetable(models.Model):
#     timecourseid = models.IntegerField(db_column='timeCourseID', primary_key=True, blank=True, null=False)  # Field name made lowercase.
#     singletrialid = models.ForeignKey(Singletrial, models.DO_NOTHING, db_column='singleTrialID', blank=True, null=True)  # Field name made lowercase.
#     titertype = models.TextField(db_column='titerType', blank=True, null=True)  # Field name made lowercase.
#     analyte_name = models.TextField(blank=True, null=True)
#     time_vector = models.BinaryField(blank=True, null=True)
#     data_vector = models.BinaryField(blank=True, null=True)
#     rate = models.BinaryField(blank=True, null=True)
#
#     class Meta:
#         managed = True
#         db_table = 'timeCourseTable'
#
#
# class TimecoursetableAvg(models.Model):
#     timecourseid = models.IntegerField(db_column='timeCourseID', primary_key=True, blank=True, null=False)  # Field name made lowercase.
#     singletrial_avgid = models.ForeignKey(SingletrialtableAvg, models.DO_NOTHING, db_column='singleTrial_avgID', blank=True, null=True)  # Field name made lowercase.
#     titertype = models.TextField(db_column='titerType', blank=True, null=True)  # Field name made lowercase.
#     analyte_name = models.TextField(blank=True, null=True)
#     time_vector = models.BinaryField(blank=True, null=True)
#     data_vector = models.BinaryField(blank=True, null=True)
#     rate = models.BinaryField(blank=True, null=True)
#
#     class Meta:
#         managed = True
#         db_table = 'timeCourseTable_avg'
#
#
# class TimecoursetableStd(models.Model):
#     timecourseid = models.IntegerField(db_column='timeCourseID', primary_key=True, blank=True, null=False)  # Field name made lowercase.
#     singletrial_stdid = models.ForeignKey(SingletrialtableStd, models.DO_NOTHING, db_column='singleTrial_stdID', blank=True, null=True)  # Field name made lowercase.
#     titertype = models.TextField(db_column='titerType', blank=True, null=True)  # Field name made lowercase.
#     analyte_name = models.TextField(blank=True, null=True)
#     time_vector = models.BinaryField(blank=True, null=True)
#     data_vector = models.BinaryField(blank=True, null=True)
#     rate = models.BinaryField(blank=True, null=True)
#
#     class Meta:
#         managed = True
#         db_table = 'timeCourseTable_std'
