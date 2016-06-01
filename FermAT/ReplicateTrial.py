from FermAT.SingleTrial import *
from FermAT.Titer import *

class ReplicateTrial(object):
    """
    This object stores SingleTrial objects and calculates statistics on these replicates for each of the
    titers which are stored within it
    """

    def __init__(self):
        self.avg = SingleTrial()
        self.std = SingleTrial()
        self.t = None
        self.singleTrialList = []
        self.runIdentifier = RunIdentifier()
        self.badReplicates = []
        self.replicateIDs = []
        # self.checkReplicateUniqueIDMatch()

    def summary(self):
        return

    def commitToDB(self, experimentID=None, c=None):
        """
        Commit to the database

        Parameters
        ----------
        experimentID : int
        c : database cursor
        """
        if experimentID == None:
            print('No experiment ID selected')
        else:
            identifier3 = ''
            c.execute("""\
               INSERT INTO replicateTable(experimentID, strainID, identifier1, identifier2, identifier3)
               VALUES (?, ?, ?, ?, ?)""",
                      (experimentID, self.runIdentifier.strainID, self.runIdentifier.identifier1,
                       self.runIdentifier.identifier2, identifier3)
                      )
            c.execute("""SELECT MAX(replicateID) FROM replicateTable""")
            replicateID = c.fetchall()[0][0]

            for singleExperiment in self.singleTrialList:
                singleExperiment.commitToDB(replicateID, c=c)
            self.avg.commitToDB(replicateID, c=c, stat='avg')
            self.std.commitToDB(replicateID, c=c, stat='std')

    def loadFromDB(self, c=None, replicateID='all'):
        """
        Load from the database.

        Parameters
        ----------
        c : sql cursor
        replicateID : int
        """
        if type(replicateID) is not (int):
            raise Exception(
                'Cannot load multiple replicates in a single call to this function, load from parent instead')

        c.execute("""SELECT * FROM replicateTable WHERE replicateID = ?""", (replicateID,))
        for row in c.fetchall():
            self.runIdentifier.strainID = row[2]
            self.runIdentifier.identifier1 = row[3]
            self.runIdentifier.identifier2 = row[4]

        c.execute(
            """SELECT singleTrialID, replicateID, replicate, yieldsDict FROM singleTrialTable WHERE replicateID = ?""",
            (replicateID,))
        for row in c.fetchall():
            self.singleTrialList.append(SingleTrial())
            self.singleTrialList[-1].yields = pickle.loads(row[3])
            self.singleTrialList[-1].runIdentifier.replicate = row[2]
            self.singleTrialList[-1].loadFromDB(c=c, singleTrialID=row[0])

        for stat in ['_avg', '_std']:
            c.execute(
                """SELECT singleTrialID""" + stat + """, replicateID, replicate, yieldsDict FROM singleTrialTable""" + stat + """ WHERE replicateID = ?""",
                (replicateID,))
            row = c.fetchall()[0]
            getattr(self, stat.replace('_', '')).loadFromDB(c=c, singleTrialID=row[0], stat=stat.replace('_', ''))

        self.t = self.singleTrialList[0].t

    def checkReplicateUniqueIDMatch(self):
        """
        Ensures that the uniqueIDs match for all te replicate experiments
        """
        for i in range(len(self.singleTrialList) - 1):
            if self.singleTrialList[i].getUniqueReplicateID() != self.singleTrialList[i + 1].getUniqueReplicateID():
                raise Exception(
                    "the replicates do not have the same uniqueID, either the uniqueID includes too much information or the strains don't match")

            if (self.singleTrialList[i].t != self.singleTrialList[i + 1].t).all():
                print(self.singleTrialList[i].t, self.singleTrialList[i + 1].t)
                raise Exception("time vectors don't match within replicates")
            else:
                self.t = self.singleTrialList[i].t

                # if len(self.singleTrialList[i].t) != len(self.singleTrialList[i + 1].t):  # TODO
                #     print("Time Vector 1: ", self.singleTrialList[i].t, "\nTime Vector 2: ", self.singleTrialList[i + 1].t)
                #     print("Vector 1: ", self.singleTrialList[i].substrate.dataVec, "\nVector 2: ",
                #           self.singleTrialList[i + 1].substrate.dataVec)
                #     raise (Exception("length of substrate vectors do not match"))
                #
                # for key in self.singleTrialList[i].products:
                #     if len(self.singleTrialList[i].products[key].dataVec) != len(
                #             self.singleTrialList[i + 1].products[key].dataVec):
                #         raise (Exception("length of product vector " + str(key) + " do not match"))

    def addReplicateExperiment(self, singleTrial):
        """
        Add a SingleTrial object to this list of replicates

        Parameters
        ----------
        singleTrial : :class:`~SingleTrial`
            Add a SingleTrial
        """

        self.singleTrialList.append(singleTrial)
        if len(self.singleTrialList) == 1:
            self.t = self.singleTrialList[0].t
        self.checkReplicateUniqueIDMatch()

        self.runIdentifier = singleTrial.runIdentifier
        self.runIdentifier.time = None
        self.replicateIDs.append(
            singleTrial.runIdentifier.replicate)  # TODO remove this redundant functionality
        self.replicateIDs.sort()
        self.calculate_statistics()

    def calculate_statistics(self):
        """
        Calculates the statistics on the SingleTrial objects
        """
        for key in [singleTrial.titerObjectDict.keys() for singleTrial in self.singleTrialList][
            0]:  # TODO Generalize this
            for stat, calc in zip(['avg', 'std'], [np.mean, np.std]):
                getattr(self, stat).titerObjectDict[key] = TimeCourseShell()
                getattr(self, stat).titerObjectDict[key].timeVec = self.t
                getattr(self, stat).titerObjectDict[key].dataVec = calc(
                    [singleExperimentObject.titerObjectDict[key].dataVec for singleExperimentObject in
                     self.singleTrialList if
                     singleExperimentObject.runIdentifier.replicate not in self.badReplicates], axis=0)
                if None not in [singleExperimentObject.titerObjectDict[key].rate for singleExperimentObject in
                                self.singleTrialList]:
                    temp = dict()
                    for param in self.singleTrialList[0].titerObjectDict[key].rate:
                        temp[param] = calc(
                            [singleExperimentObject.titerObjectDict[key].rate[param] for singleExperimentObject in
                             self.singleTrialList if
                             singleExperimentObject.runIdentifier.replicate not in self.badReplicates])
                    getattr(self, stat).titerObjectDict[key].rate = temp
                getattr(self, stat).titerObjectDict[key].runIdentifier = self.singleTrialList[0].titerObjectDict[
                    key].runIdentifier

        if self.singleTrialList[0].yields:  # TODO Should make this general by checking for the existance of any yields
            for key in self.singleTrialList[0].yields:
                self.avg.yields[key] = np.mean(
                    [singleExperimentObject.yields[key] for singleExperimentObject in self.singleTrialList], axis=0)
                self.std.yields[key] = np.std(
                    [singleExperimentObject.yields[key] for singleExperimentObject in self.singleTrialList], axis=0)