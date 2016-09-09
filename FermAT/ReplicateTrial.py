import numpy as np
import dill as pickle
import pandas as pd
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

            # Deprecated as of v0.5.0, pandas allows dealing with data with different shapes
            # if (self.single_trial_list[i].t != self.single_trial_list[i + 1].t).all():
            #     print(self.single_trial_list[i].t, self.single_trial_list[i + 1].t)
            #     raise Exception("time vectors don't match within replicates")
            # else:
            #     self.t = self.single_trial_list[i].t

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
        if singleTrial.trial_identifier.replicate_id not in self.replicate_ids:
            self.replicate_ids.append(
                singleTrial.trial_identifier.replicate_id)  # TODO remove this redundant functionality
        else:
            raise Exception('Duplicate replicate id: '
                            + singleTrial.trial_identifier.replicate_id
                            + '.\nCurrent ids: '
                            + self.replicate_ids)
        try:
            self.replicate_ids.sort()
        except Exception as e:
            print(e)
            print(self.replicate_ids)

        self.calculate_statistics()

    def calculate_statistics(self):
        """
        Calculates the statistics on the SingleTrial objects
        """
        # Get all unique titers
        unique_analytes = []
        for single_trial in self.single_trial_list:
            for titer in single_trial.titerObjectDict:
                unique_analytes.append(titer)

        unique_analytes = list(set(unique_analytes))

        # analyte_df = pd.DataFrame()
        for analyte in unique_analytes:
            for stat, calc in zip(['avg', 'std'], [np.mean, np.std]):
                getattr(self, stat).titerObjectDict[analyte] = TimeCourseShell()
                # getattr(self, stat).titerObjectDict[analyte].time_vector = self.t

                try:
                    # # Depricated non pd implementation
                    # getattr(self, stat).titerObjectDict[analyte].data_vector = calc(
                    #     [singleExperimentObject.titerObjectDict[analyte].data_vector
                    #      for singleExperimentObject in self.single_trial_list if
                    #      singleExperimentObject.trial_identifier.replicate_id not in self.bad_replicates], axis=0)

                    # pd
                    # Build the df from all the replicates
                    analyte_df = pd.DataFrame()

                    # Only iterate through single trials with the analyte of interest
                    temp_single_trial_list = [single_trial for single_trial in self.single_trial_list if analyte in single_trial.titerObjectDict]
                    for single_trial in temp_single_trial_list:
                        temp_analyte_df = pd.DataFrame(
                            {single_trial.trial_identifier.replicate_id: single_trial.titerObjectDict[analyte].pd_series})

                        # Merging the dataframes this way will allow different time indices for different analytes
                        analyte_df = pd.merge(analyte_df,
                                              temp_analyte_df,
                                              left_index=True,
                                              right_index=True,
                                              how='outer')
                        # analyte_df[single_trial.trial_identifier.replicate_id] = single_trial.titerObjectDict[analyte].pd_series

                    # Save the mean or std
                    if stat == 'avg':
                        getattr(self, stat).titerObjectDict[analyte].pd_series = analyte_df.mean(axis=1)
                    elif stat == 'std':
                        getattr(self, stat).titerObjectDict[analyte].pd_series = analyte_df.std(axis=1)
                    else:
                        raise Exception('Unknown statistic type')

                    #To maintain backward compatabaility
                    getattr(self, stat).titerObjectDict[analyte]._time_vector = np.array(getattr(self, stat).titerObjectDict[analyte].pd_series.index)
                    getattr(self, stat).titerObjectDict[analyte]._data_vector = np.array(getattr(self, stat).titerObjectDict[analyte].pd_series)

                    # print(stat)
                    # print('df:')
                    # print(analyte_df.head())
                    # print('mean series:')
                    # print(getattr(self, stat).titerObjectDict[analyte].pd_series.head())
                except Exception as e:
                    print(e)
                    print([singleExperimentObject.titerObjectDict[analyte].data_vector
                         for singleExperimentObject in self.single_trial_list if
                         singleExperimentObject.trial_identifier.replicate_id not in self.bad_replicates])

                # If a rate exists, calculate the mean
                if None not in [singleExperimentObject.titerObjectDict[analyte].rate
                                for singleExperimentObject in self.single_trial_list]:
                    temp = dict()
                    for param in self.single_trial_list[0].titerObjectDict[analyte].rate:
                        temp[param] = calc(
                            [singleExperimentObject.titerObjectDict[analyte].rate[param] for singleExperimentObject in
                             self.single_trial_list if
                             singleExperimentObject.trial_identifier.replicate_id not in self.bad_replicates])
                    getattr(self, stat).titerObjectDict[analyte].rate = temp
                getattr(self, stat).titerObjectDict[analyte].trial_identifier = self.single_trial_list[0].titerObjectDict[
                    analyte].trial_identifier


        # Get all unique yields
        unique_yields = []
        for single_trial in self.single_trial_list:
            for analyte in single_trial.yields:
                unique_yields.append(analyte)
        unique_yields = list(set(unique_analytes))

        # Calculate statistics for each
        for analyte in unique_yields:
            temp_single_trial_list = [single_trial for single_trial in self.single_trial_list if
                                      analyte in single_trial.yields]
            yield_df = pd.DataFrame()
            for single_trial in temp_single_trial_list:
                temp_yield_df = pd.DataFrame({single_trial.trial_identifier.replicate_id: single_trial.yields[analyte]})
                yield_df = pd.merge(yield_df,
                                    temp_yield_df,
                                      left_index=True,
                                      right_index=True,
                                      how='outer')

            # Save the mean or std
            if stat == 'avg':
                self.avg.yields[analyte] = np.array(yield_df.mean(axis=1))
            elif stat == 'std':
                self.avg.yields[analyte] = np.array(yield_df.std(axis=1))
            else:
                raise Exception('Unknown statistic type')

            # Deprecated since v0.5.0
            # self.avg.yields[key] = np.mean(
            #     [singleExperimentObject.yields[key] for singleExperimentObject in self.single_trial_list], axis=0)
            # self.std.yields[key] = np.std(
            #     [singleExperimentObject.yields[key] for singleExperimentObject in self.single_trial_list], axis=0)
