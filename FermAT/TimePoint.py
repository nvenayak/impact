from FermAT.TrialIdentifier import RunIdentifier
import sqlite3 as sql

class TimePoint(object):
    def __init__(self, runID, titerName, t, titer):
        self.runIdentifier = runID
        self.titerName = titerName
        self.t = t
        self.titer = titer
        self.units = {'t'    : 'h',
                      'titer': 'g'}

    def getUniqueTimePointID(self):
        return self.runIdentifier.strainID + self.runIdentifier.identifier1 + self.runIdentifier.identifier2 + str(
            self.runIdentifier.replicate) + self.runIdentifier.titerName