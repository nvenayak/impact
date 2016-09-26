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
        runID = self.trial_identifier
        # print(runID.strain_id)
        # print(runID.id_1)
        # print(runID.id_2)
        # print(str(runID.replicate_id))
        # print(runID.analyte_name)
        return self.trial_identifier.strain_id + self.trial_identifier.id_1 + self.trial_identifier.id_2 + str(
            self.trial_identifier.replicate_id) + self.trial_identifier.analyte_name
