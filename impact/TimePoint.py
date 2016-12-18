# from .TrialIdentifier import trial_identifier
# import sqlite3 as sql

class TimePoint(object):
    def __init__(self, runID, analyte_name, t, titer):
        self.trial_identifier = runID
        self.analyte_name = analyte_name
        self.t = t
        self.titer = titer
        self.units = {'t'    : 'h',
                      'titer': 'g'}

    def get_unique_timepoint_id(self):
        return self.trial_identifier.strain_id + self.trial_identifier.id_1 + self.trial_identifier.id_2 + str(
            self.trial_identifier.replicate_id) + self.trial_identifier.analyte_name
