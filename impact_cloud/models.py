# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from __future__ import unicode_literals

from django.db import models


class Analyte(models.Model):
    name = models.TextField(primary_key=True)  # This field type is a guess.
    default_type = models.TextField(blank=True, null=True)  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'analyte'


class CompConc(models.Model):
    media_name = models.ForeignKey('Media', models.DO_NOTHING, db_column='media_name', primary_key=True)
    component_name = models.ForeignKey('MediaComponent', models.DO_NOTHING, db_column='component_name', primary_key=True)
    concentration = models.TextField(blank=True, null=True)  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'comp_conc'
        unique_together = (('media_name', 'component_name'),)


class Experiment(models.Model):
    id = models.IntegerField(primary_key=True)  # AutoField?

    class Meta:
        managed = False
        db_table = 'experiment'


class FitParameters(models.Model):
    id = models.IntegerField(primary_key=True)  # AutoField?
    parent = models.ForeignKey('TimeCourse', models.DO_NOTHING, db_column='parent', blank=True, null=True)
    parameter_name = models.TextField(blank=True, null=True)  # This field type is a guess.
    parameter_value = models.TextField(blank=True, null=True)  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'fit_parameters'


class Media(models.Model):
    name = models.TextField(primary_key=True)  # This field type is a guess.
    parent = models.ForeignKey('self', models.DO_NOTHING, db_column='parent', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'media'


class MediaComponent(models.Model):
    name = models.TextField(primary_key=True)  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'media_component'


class ReplicateTrial(models.Model):
    id = models.IntegerField(primary_key=True)  # AutoField?
    avg = models.ForeignKey('SingleTrial', models.DO_NOTHING, blank=True, null=True)
    std = models.ForeignKey('SingleTrial', models.DO_NOTHING, blank=True, null=True)
    trial_identifier = models.ForeignKey('TrialIdentifier', models.DO_NOTHING, blank=True, null=True)
    stage_parent = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    blank = models.ForeignKey('SingleTrial', models.DO_NOTHING, blank=True, null=True)
    parent = models.ForeignKey(Experiment, models.DO_NOTHING, blank=True, null=True)
    bad_replicates = models.BinaryField(blank=True, null=True)
    replicate_ids = models.BinaryField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'replicate_trial'


class Settings(models.Model):
    id = models.IntegerField(primary_key=True)  # AutoField?
    verbose = models.NullBooleanField()
    live_calculations = models.NullBooleanField()
    remove_death_phase_flag = models.NullBooleanField()
    use_filtered_data = models.NullBooleanField()
    minimum_points_for_curve_fit = models.IntegerField(blank=True, null=True)
    savgolfilterwindowsize = models.IntegerField(db_column='savgolFilterWindowSize', blank=True, null=True)  # Field name made lowercase.
    perform_curve_fit = models.NullBooleanField()
    max_fraction_replicates_to_remove = models.TextField(blank=True, null=True)  # This field type is a guess.
    default_outlier_cleaning_flag = models.NullBooleanField()
    outlier_cleaning_flag = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'settings'


class SingleTrial(models.Model):
    id = models.IntegerField(primary_key=True)  # AutoField?
    trial_identifier = models.ForeignKey('TrialIdentifier', models.DO_NOTHING, blank=True, null=True)
    field_substrate_name = models.BinaryField(db_column='_substrate_name', blank=True, null=True)  # Field renamed because it started with '_'.
    stage_indices = models.BinaryField(blank=True, null=True)
    parent = models.ForeignKey(ReplicateTrial, models.DO_NOTHING, blank=True, null=True)
    stage_parent = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    normalized_data = models.BinaryField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'single_trial'


class Stage(models.Model):
    id = models.IntegerField(primary_key=True)  # AutoField?
    start_time = models.TextField(blank=True, null=True)  # This field type is a guess.
    end_time = models.TextField(blank=True, null=True)  # This field type is a guess.
    parent = models.ForeignKey(Experiment, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stage'


class Strain(models.Model):
    id = models.IntegerField(primary_key=True)  # AutoField?
    name = models.TextField(blank=True, null=True)  # This field type is a guess.
    plasmid_1 = models.TextField(blank=True, null=True)  # This field type is a guess.
    plasmid_2 = models.TextField(blank=True, null=True)  # This field type is a guess.
    plasmid_3 = models.TextField(blank=True, null=True)  # This field type is a guess.

    class Meta:
        managed = False
        db_table = 'strain'


class TimeCourse(models.Model):
    discriminator = models.CharField(max_length=50, blank=True, null=True)
    id = models.IntegerField(primary_key=True)  # AutoField?
    trial_identifier = models.ForeignKey('TrialIdentifier', models.DO_NOTHING, blank=True, null=True)
    calculations_uptodate = models.NullBooleanField()
    parent = models.ForeignKey(SingleTrial, models.DO_NOTHING, blank=True, null=True)
    analyte_name = models.TextField(blank=True, null=True)  # This field type is a guess.
    analyte_type = models.TextField(blank=True, null=True)  # This field type is a guess.
    stage_parent = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'time_course'


class TimePoint(models.Model):
    time_point_type = models.TextField(blank=True, null=True)  # This field type is a guess.
    id = models.IntegerField(primary_key=True)  # AutoField?
    trial_identifier = models.ForeignKey('TrialIdentifier', models.DO_NOTHING, blank=True, null=True)
    time = models.TextField(blank=True, null=True)  # This field type is a guess.
    data = models.TextField(blank=True, null=True)  # This field type is a guess.
    parent = models.ForeignKey(TimeCourse, models.DO_NOTHING, blank=True, null=True)
    use_in_analysis = models.NullBooleanField()

    class Meta:
        managed = False
        db_table = 'time_point'


class TrialIdentifier(models.Model):
    id = models.IntegerField(primary_key=True)  # AutoField?
    strain = models.ForeignKey(Strain, models.DO_NOTHING, blank=True, null=True)
    media_name = models.ForeignKey(Media, models.DO_NOTHING, db_column='media_name', blank=True, null=True)
    replicate_id = models.IntegerField(blank=True, null=True)
    analyte_name = models.ForeignKey(Analyte, models.DO_NOTHING, db_column='analyte_name', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'trial_identifier'
