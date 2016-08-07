# from .TrialIdentifier import RunIdentifier
# import sqlite3 as sql

class TimePoint(object):
    def __init__(self, runID, analyte_name, t, titer):
        self.runIdentifier = runID
        self.analyte_name = analyte_name
        self.t = t
        self.titer = titer
        self.units = {'t'    : 'h',
                      'titer': 'g'}

    def get_unique_timepoint_id(self):
        runID = self.runIdentifier
        # print(runID.strain_id)
        # print(runID.id_1)
        # print(runID.id_2)
        # print(str(runID.replicate_id))
        # print(runID.analyte_name)
        return self.runIdentifier.strain_id + self.runIdentifier.id_1 + self.runIdentifier.id_2 + str(
            self.runIdentifier.replicate_id) + self.runIdentifier.analyte_name
