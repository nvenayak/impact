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
        self.bad_replicates = []
        self.replicate_ids = []
        # self.checkReplicateUniqueIDMatch()

        self.stages = []

    def calculate_stages(self, stage_indices = None):
        if stage_indices is None:
            raise Exception('No stage_indices provided')

        self.stages = []
        self.stage_indices = stage_indices

        for stage_bounds in stage_indices:
            print(stage_bounds)
            self.stages.append(self.create_stage(stage_bounds))


    def create_stage(self, stage_bounds):
        stage = ReplicateTrial()
        for singleTrial in self.singleTrialList:
            stage.add_replicate(singleTrial.create_stage(stage_bounds))

        return stage

    def summary(self):
        return

    def get_normalize_data(self, normalize_to):
        new_replicate = ReplicateTrial()
        for trial in self.singleTrialList:
            trial.normalize_data(normalize_to)
            new_replicate.add_replicate(trial)
        self = new_replicate

    def db_commit(self, experimentID=None, c=None):
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
                singleExperiment.db_commit(replicateID, c=c)
            self.avg.db_commit(replicateID, c=c, stat='avg')
            self.std.db_commit(replicateID, c=c, stat='std')

    def db_load(self, c=None, replicateID='all'):
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
            self.singleTrialList[-1].db_load(c=c, singleTrialID=row[0])

        for stat in ['_avg', '_std']:
            c.execute(
                """SELECT singleTrialID""" + stat + """, replicateID, replicate, yieldsDict FROM singleTrialTable""" + stat + """ WHERE replicateID = ?""",
                (replicateID,))
            row = c.fetchall()[0]
            getattr(self, stat.replace('_', '')).db_load(c=c, singleTrialID=row[0], stat=stat.replace('_', ''))

        self.t = self.singleTrialList[0].t

    def check_replicate_unique_id_match(self):
        """
        Ensures that the uniqueIDs match for all te replicate experiments
        """
        for i in range(len(self.singleTrialList) - 1):
            if self.singleTrialList[i].get_unique_replicate_id() != self.singleTrialList[i + 1].get_unique_replicate_id():
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

    def add_replicate(self, singleTrial):
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
            self.stage_indices = self.singleTrialList[0].stage_indices


            for stat in ['avg', 'std']:
                getattr(self, stat)._substrate_name = self.singleTrialList[0].substrate_name
                getattr(self, stat).product_names = self.singleTrialList[0].product_names
                getattr(self, stat).biomass_name = self.singleTrialList[0].biomass_name
                # getattr(self, stat).stages = self.singleTrialList[0].stages

        self.check_replicate_unique_id_match()

        self.runIdentifier = singleTrial.runIdentifier
        self.runIdentifier.time = None
        self.replicate_ids.append(
            singleTrial.runIdentifier.replicate)  # TODO remove this redundant functionality
        self.replicate_ids.sort()
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
                     singleExperimentObject.runIdentifier.replicate not in self.bad_replicates], axis=0)
                if None not in [singleExperimentObject.titerObjectDict[key].rate for singleExperimentObject in
                                self.singleTrialList]:
                    temp = dict()
                    for param in self.singleTrialList[0].titerObjectDict[key].rate:
                        temp[param] = calc(
                            [singleExperimentObject.titerObjectDict[key].rate[param] for singleExperimentObject in
                             self.singleTrialList if
                             singleExperimentObject.runIdentifier.replicate not in self.bad_replicates])
                    getattr(self, stat).titerObjectDict[key].rate = temp
                getattr(self, stat).titerObjectDict[key].runIdentifier = self.singleTrialList[0].titerObjectDict[
                    key].runIdentifier

        if self.singleTrialList[0].yields:  # TODO Should make this general by checking for the existance of any yields
            for key in self.singleTrialList[0].yields:
                self.avg.yields[key] = np.mean(
                    [singleExperimentObject.yields[key] for singleExperimentObject in self.singleTrialList], axis=0)
                self.std.yields[key] = np.std(
                    [singleExperimentObject.yields[key] for singleExperimentObject in self.singleTrialList], axis=0)