import numpy as np
import dill as pickle

from .SingleTrial import SingleTrial
from .AnalyteData import TimeCourseShell
from .TrialIdentifier import TrialIdentifier


class ReplicateTrial(object):
    """
    This object stores SingleTrial objects and calculates statistics on these replicates for each of the
    titers which are stored within it
    """

    def __init__(self):
        self.avg = SingleTrial()
        self.std = SingleTrial()
        self.t = None
        self.single_trial_list = []
        self.trial_identifier = TrialIdentifier()
        self.bad_replicates = []
        self.replicate_ids = []
        # self.checkReplicateUniqueIDMatch()

        self.stages = []

    # def summary(self):
    #     for single_trial in self.single_trial_list:
    #

    def calculate_stages(self, stage_indices=None):
        if stage_indices is None:
            raise Exception('No stage_indices provided')

        self.stages = []
        self.stage_indices = stage_indices

        for stage_bounds in stage_indices:
            print(stage_bounds)
            self.stages.append(self.create_stage(stage_bounds))

    def create_stage(self, stage_bounds):
        stage = ReplicateTrial()
        for singleTrial in self.single_trial_list:
            stage.add_replicate(singleTrial.create_stage(stage_bounds))

        return stage

    def summary(self):
        return

    def get_normalize_data(self, normalize_to):
        new_replicate = ReplicateTrial()
        for trial in self.single_trial_list:
            trial.normalize_data(normalize_to)
            new_replicate.add_replicate(trial)
        self = new_replicate

    def db_commit(self, experiment_id=None, c=None):
        """
        Commit to the database

        Parameters
        ----------
        experiment_id : int
        c : database cursor
        """
        if experiment_id == None:
            print('No experiment ID selected')
        else:
            id_3 = ''
            c.execute("""\
               INSERT INTO replicateTable(experiment_id, strain_id, id_1, id_2, id_3)
               VALUES (?, ?, ?, ?, ?)""",
                      (experiment_id, self.trial_identifier.strain_id, self.trial_identifier.id_1,
                       self.trial_identifier.id_2, id_3)
                      )
            c.execute("""SELECT MAX(replicateID) FROM replicateTable""")
            replicateID = c.fetchall()[0][0]

            for singleExperiment in self.single_trial_list:
                singleExperiment.db_commit(replicateID, c=c)
            self.avg.db_commit(replicateID, c=c, stat='avg')
            self.std.db_commit(replicateID, c=c, stat='std')

    def db_load(self, c=None, db_name = None, replicateID='all'):
        """
        Load from the database.

        Parameters
        ----------
        c : sql cursor
        replicateID : int
        """

        if c is None:
            if db_name is None:
                raise Exception('Need either a cursor or db name')
            import sqlite3 as sql
            conn = sql.connect(db_name)
            c = conn.cursor()
            close_conn = True
        else:
            close_conn = False

        if type(replicateID) is not (int):
            raise Exception(
                'Cannot load multiple replicates in a single call to this function, load from parent instead')

        c.execute("""SELECT * FROM replicateTable WHERE replicateID = ?""", (replicateID,))
        for row in c.fetchall():
            self.trial_identifier.strain_id = row[2]
            self.trial_identifier.id_1 = row[3]
            self.trial_identifier.id_2 = row[4]
            self.db_replicate_id = row[0]

        c.execute(
            """SELECT singleTrialID, replicateID, replicate_id, yieldsDict FROM singleTrialTable WHERE replicateID = ?""",
            (replicateID,))
        for row in c.fetchall():
            self.single_trial_list.append(SingleTrial())
            self.single_trial_list[-1].yields = pickle.loads(row[3])
            self.single_trial_list[-1].trial_identifier = self.trial_identifier
            self.single_trial_list[-1].trial_identifier.replicate_id = row[2]
            self.single_trial_list[-1].db_load(c=c, singleTrialID=row[0])

        for stat in ['_avg', '_std']:
            c.execute(
                """SELECT singleTrialID""" + stat + """, replicateID, replicate_id, yieldsDict FROM singleTrialTable""" + stat + """ WHERE replicateID = ?""",
                (replicateID,))
            row = c.fetchall()[0]
            getattr(self, stat.replace('_', '')).db_load(c=c, singleTrialID=row[0], stat=stat.replace('_', ''))

        self.t = self.single_trial_list[0].t

        if close_conn:
            conn.close()

    def check_replicate_unique_id_match(self):
        """
        Ensures that the uniqueIDs match for all te replicate_id experiments
        """
        for i in range(len(self.single_trial_list) - 1):
            if self.single_trial_list[i].get_unique_replicate_id() != self.single_trial_list[
                        i + 1].get_unique_replicate_id():
                raise Exception(
                    "the replicates do not have the same uniqueID, either the uniqueID includes too much information or the strains don't match")

            if (self.single_trial_list[i].t != self.single_trial_list[i + 1].t).all():
                print(self.single_trial_list[i].t, self.single_trial_list[i + 1].t)
                raise Exception("time vectors don't match within replicates")
            else:
                self.t = self.single_trial_list[i].t

                # if len(self.single_trial_list[i].t) != len(self.single_trial_list[i + 1].t):  # TODO
                #     print("Time Vector 1: ", self.single_trial_list[i].t, "\nTime Vector 2: ", self.single_trial_list[i + 1].t)
                #     print("Vector 1: ", self.single_trial_list[i].substrate.data_vector, "\nVector 2: ",
                #           self.single_trial_list[i + 1].substrate.data_vector)
                #     raise (Exception("length of substrate vectors do not match"))
                #
                # for key in self.single_trial_list[i].products:
                #     if len(self.single_trial_list[i].products[key].data_vector) != len(
                #             self.single_trial_list[i + 1].products[key].data_vector):
                #         raise (Exception("length of product vector " + str(key) + " do not match"))

    def add_replicate(self, singleTrial):
        """
        Add a SingleTrial object to this list of replicates

        Parameters
        ----------
        singleTrial : :class:`~SingleTrial`
            Add a SingleTrial
        """

        self.single_trial_list.append(singleTrial)
        if len(self.single_trial_list) == 1:
            self.t = self.single_trial_list[0].t
            self.stage_indices = self.single_trial_list[0].stage_indices

            for stat in ['avg', 'std']:
                getattr(self, stat)._substrate_name = self.single_trial_list[0].substrate_name
                getattr(self, stat).product_names = self.single_trial_list[0].product_names
                getattr(self, stat).biomass_name = self.single_trial_list[0].biomass_name
                # getattr(self, stat).stages = self.single_trial_list[0].stages

        self.check_replicate_unique_id_match()

        self.trial_identifier = singleTrial.trial_identifier
        self.trial_identifier.time = None
        self.replicate_ids.append(
            singleTrial.trial_identifier.replicate_id)  # TODO remove this redundant functionality
        try:
            self.replicate_ids.sort()
        except Exception:
            print(self.replicate_ids)
        self.calculate_statistics()

    def calculate_statistics(self):
        """
        Calculates the statistics on the SingleTrial objects
        """
        for key in [singleTrial.titerObjectDict.keys() for singleTrial in self.single_trial_list][
            0]:  # TODO Generalize this
            for stat, calc in zip(['avg', 'std'], [np.mean, np.std]):
                getattr(self, stat).titerObjectDict[key] = TimeCourseShell()
                getattr(self, stat).titerObjectDict[key].time_vector = self.t
                try:
                    getattr(self, stat).titerObjectDict[key].data_vector = calc(
                        [singleExperimentObject.titerObjectDict[key].data_vector
                         for singleExperimentObject in self.single_trial_list if
                         singleExperimentObject.trial_identifier.replicate_id not in self.bad_replicates], axis=0)
                except Exception as e:
                    print([singleExperimentObject.titerObjectDict[key].data_vector
                         for singleExperimentObject in self.single_trial_list if
                         singleExperimentObject.trial_identifier.replicate_id not in self.bad_replicates])
                if None not in [singleExperimentObject.titerObjectDict[key].rate for singleExperimentObject in
                                self.single_trial_list]:
                    temp = dict()
                    for param in self.single_trial_list[0].titerObjectDict[key].rate:
                        temp[param] = calc(
                            [singleExperimentObject.titerObjectDict[key].rate[param] for singleExperimentObject in
                             self.single_trial_list if
                             singleExperimentObject.trial_identifier.replicate_id not in self.bad_replicates])
                    getattr(self, stat).titerObjectDict[key].rate = temp
                getattr(self, stat).titerObjectDict[key].trial_identifier = self.single_trial_list[0].titerObjectDict[
                    key].trial_identifier

        if self.single_trial_list[
            0].yields:  # TODO Should make this general by checking for the existance of any yields
            for key in self.single_trial_list[0].yields:
                self.avg.yields[key] = np.mean(
                    [singleExperimentObject.yields[key] for singleExperimentObject in self.single_trial_list], axis=0)
                self.std.yields[key] = np.std(
                    [singleExperimentObject.yields[key] for singleExperimentObject in self.single_trial_list], axis=0)
