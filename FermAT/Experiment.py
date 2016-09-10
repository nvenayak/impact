from .TimePoint import TimePoint
from .AnalyteData import TimeCourse
from .TrialIdentifier import TrialIdentifier
from .SingleTrial import SingleTrial
from .ReplicateTrial import ReplicateTrial

from . import parsers

import sqlite3 as sql

import time
import copy

try:
    from pyexcel_xlsx import get_data
except ImportError as e:
    print('Could not import pyexcel')
    print(e)
    pass

import matplotlib.pyplot as plt
import numpy as np

class Experiment(object):
    # colorMap = 'Set2'

    def __init__(self, info=None):
        # Initialize variables
        self.timepoint_list = []  # dict()
        self.titer_dict = dict()
        self.single_experiment_dict = dict()
        self.replicate_experiment_dict = dict()
        self.info_keys = ['import_date', 'experiment_start_date', 'experiment_end_date', 'experiment_title', 'primary_scientist_name',
                          'secondary_scientist_name', 'medium_base', 'medium_supplements', 'notes']
        if info is not None:
            self.info = {key: info[key] for key in self.info_keys if key in info}
        else:
            self.info = dict()

    def __add__(self, experiment):
        """
        Add the experiments together by breaking them down to the analyte data and rebuilding to experiments.

        Parameters
        ----------
        experiment
        """
        # Break the experiment into its titer components
        titer_list = []
        for replicateExperiment in self.replicate_experiment_dict:
            for singleTrial in self.replicate_experiment_dict[replicateExperiment].single_trial_list:
                for titer in singleTrial.titerObjectDict:
                    titer_list.append(singleTrial.titerObjectDict[titer])

        for replicateExperiment in experiment.replicate_experiment_dict:
            for singleTrial in experiment.replicate_experiment_dict[replicateExperiment].single_trial_list:
                for titer in singleTrial.titerObjectDict:
                    titer_list.append(singleTrial.titerObjectDict[titer])

        combined_experiment = Experiment()
        combined_experiment.info = self.info
        combined_experiment.parse_titers(titer_list)

        return combined_experiment

    def db_commit(self, db_name, overwrite_experiment_id = None):
        """
        Commit the experiment to the database

        Parameters
        ----------
        db_name : str
            Path to the database, must be initialized prior (FermAT.init_db())
        """
        conn = sql.connect(db_name)
        c = conn.cursor()

        # Ensure the experiment_id is not explicitely defined (may have been defined in a form via django)
        if 'experiment_id' in self.info.keys():
            del self.info['experiment_id']

        prepared_columns = list(self.info.keys())
        prepped_column_query = ', '.join(col for col in prepared_columns)
        prepped_column_data = [self.info[key] for key in prepared_columns]


        if overwrite_experiment_id is None:
            c.execute("""INSERT INTO experimentTable (""" + prepped_column_query + \
                      """) VALUES (""" + ', '.join('?' for a in prepped_column_data) + """)""", prepped_column_data)
            c.execute("SELECT MAX(experiment_id) FROM experimentTable")
            experiment_id = c.fetchall()[0][0]
        elif type(overwrite_experiment_id) is int:
            experiment_id = overwrite_experiment_id
            for i, col in enumerate(prepared_columns):
                c.execute("""UPDATE experimentTable SET """
                          + col + """ = ? WHERE experiment_id = ?""", (prepped_column_data[i],experiment_id)
                          )

        for key in self.replicate_experiment_dict:
            self.replicate_experiment_dict[key].db_commit(experiment_id, c=c)

        conn.commit()
        c.close()

        print('Committed experiment #', experiment_id, ' to DB ', db_name)
        return experiment_id

    def db_load(self, db_name, experiment_id):
        """
        Load an experiment from the database.

        Parameters
        ----------
        db_name : str
            Path to the database, must be initialized prior (FermAT.init_db())
        experiment_id : int
            id of experiment to load
        """
        conn = sql.connect(db_name)
        c = conn.cursor()
        c.execute("""SELECT * FROM experimentTable WHERE (experiment_id == ?)""", (experiment_id,))
        self.info = {key: data for data, key in zip(c.fetchall()[0], [elem[0] for elem in c.description])}

        # Build the replicate_id experiment objects
        c.execute("""SELECT  strain_id, id_1, id_2, id_3, replicateID FROM replicateTable
                WHERE experiment_id == ?""", (experiment_id,))
        for row in c.fetchall():
            self.replicate_experiment_dict[row[0] + row[1] + row[2]] = ReplicateTrial()
            self.replicate_experiment_dict[row[0] + row[1] + row[2]].trial_identifier.strain_id = row[0]
            self.replicate_experiment_dict[row[0] + row[1] + row[2]].trial_identifier.id_1 = row[1]
            self.replicate_experiment_dict[row[0] + row[1] + row[2]].trial_identifier.id_2 = row[2]
            self.replicate_experiment_dict[row[0] + row[1] + row[2]].trial_identifier.identifier3 = row[3]
            self.replicate_experiment_dict[row[0] + row[1] + row[2]].db_load(c=c, replicateID=row[4])

        c.close()


    def db_delete(self, db_name, experiment_id):
        """
        Delete an experiment from the database.

        Parameters
        ----------
        db_name : str
            Path to the database, must be initialized prior (FermAT.init_db())
        experiment_id : int
            id of experiment to load
        """
        conn = sql.connect(db_name)
        c = conn.cursor()
        c.execute("""DELETE FROM experimentTable WHERE (experiment_id == ?)""", (experiment_id,))
        conn.commit()
        c.close()

    def data(self):
        data = []
        for replicate_key in self.replicate_experiment_dict:
            data.append([replicate_key])
            single_trial = self.replicate_experiment_dict[replicate_key].single_trial_list[0]
            for titer_key in [single_trial.biomass_name] + \
                    [single_trial.substrate_name] + \
                    single_trial.product_names:
                data.append([titer_key])

                # With pd
                print(self.replicate_experiment_dict[replicate_key].analyte_df.head())
                data.append(['Time (hours)'] + list(self.replicate_experiment_dict[replicate_key].analyte_df.index))
                for col in self.replicate_experiment_dict[replicate_key].analyte_df:
                    data.append(['rep #'
                                 + str(col)]
                                 + list(self.replicate_experiment_dict[replicate_key].analyte_df[col]))
                # print(self.replicate_experiment_dict[replicate_key].avg.analyte_df)
                data.append(['Average'] + list(
                    self.replicate_experiment_dict[replicate_key].avg.titerObjectDict[titer_key].pd_series))
                data.append(['Std'] + list(
                    self.replicate_experiment_dict[replicate_key].std.titerObjectDict[titer_key].pd_series))

                # # Without pd
                # for i, single_trial in enumerate(self.replicate_experiment_dict[replicate_key].single_trial_list):
                #     # data.append([single_trial.trial_identifier.replicate_id])
                #     if titer_key is not None:
                #         if i == 0:
                #             data.append(['Time (hours)'] + list(single_trial.titerObjectDict[titer_key].time_vector))
                #         data.append(['rep #' + str(single_trial.trial_identifier.replicate_id)] + list(
                #             single_trial.titerObjectDict[titer_key].data_vector))
                # if titer_key is not None:
                #     data.append(['Average'] + list(
                #         self.replicate_experiment_dict[replicate_key].avg.titerObjectDict[titer_key].data_vector))
                #     data.append(['Std'] + list(
                #         self.replicate_experiment_dict[replicate_key].std.titerObjectDict[titer_key].data_vector))

                # Add spacing between the titers
                data.append([])
            # Add spacing between the replicates
            data.append([])
            data.append([])

        # Remove the last three rows which will be excess if it is the last row to be written
        del data[-1]
        del data[-1]
        del data[-1]

        return data

    def get_strains_django(self, dbName, experiment_id):
        """
        Get info for all the strains in the database, used by django front end

        Parameters
        ----------
        dbName : str
            Path to the database, must be initialized prior (FermAT.init_db())
        experiment_id : int
            id of experiment to load

        Returns
        -------
        strainDescriptions : list
            List of strain info for each strain
        """
        conn = sql.connect(dbName)
        c = conn.cursor()
        c.execute("""SELECT * FROM experimentTable WHERE (experiment_id == ?)""", (experiment_id,))
        exptDescription = {key: data for data, key in zip(c.fetchall()[0], [elem[0] for elem in c.description])}

        # Build the replicate_id experiment objects
        c.execute("""SELECT  strain_id, id_1, id_2, id_3, replicateID, experiment_id FROM replicateTable
                WHERE experiment_id == ? ORDER BY strain_id DESC, id_1 DESC, id_2 DESC""", (experiment_id,))
        strainDescriptions = []
        for row in c.fetchall():
            strainDescriptions.append({key: data for data, key in zip(row, [elem[0] for elem in c.description])})
        c.close()
        return strainDescriptions

    def summary(self, level=None):
        for replicate_key in self.replicate_experiment_dict:
            self.replicate_experiment_dict[replicate_key].summary()

    def plottingGUI(self):
        app = QtGui.QApplication(sys.argv)

        main = Window(self)
        main.showMaximized()

        sys.exit(app.exec_())

    def get_strains(self):
        temp = [key for key in self.replicate_experiment_dict if
                self.replicate_experiment_dict[key].trial_identifier.id_1 != '']
        temp.sort()
        return temp

    def get_titers(self):
        titersToPlot = [[[titer for titer in singleExperiment.titerObjectDict] for singleExperiment in
                         self.replicate_experiment_dict[key].single_trial_list] for key in
                        self.replicate_experiment_dict]

        # Flatten list and find the uniques
        titersToPlot = [y for x in titersToPlot for y in x]
        titersToPlot = list(set([y for x in titersToPlot for y in x]))

        return titersToPlot

    def parseRawData(self, dataFormat, fileName=None, data=None, stage_indices=None, substrate_name=None):
        t0 = time.time()

        if data == None:
            if fileName == None:
                raise Exception('No data or file name given to load data from')

            # Get data from xlsx file
            data = get_data(fileName)
            # print(data)
            print('Imported data from %s' % (fileName))

        if dataFormat == 'NV_OD':
            t0 = time.time()
            if fileName:
                # Check for correct data for import
                if 'OD' not in data.keys():
                    raise Exception("No sheet named 'OD' found")
                else:
                    ODDataSheetName = 'OD'

                data = data[ODDataSheetName]

            # Parse data into timeCourseObjects
            skipped_lines = 0
            timeCourseObjectList = dict()
            for row in data[1:]:
                temp_run_identifier_object = TrialIdentifier()
                if type(row[0]) is str:
                    temp_run_identifier_object.parse_trial_identifier_from_csv(row[0])
                    temp_run_identifier_object.analyte_name = 'OD600'
                    temp_run_identifier_object.analyte_type = 'biomass'
                    temp_time_course = TimeCourse()
                    temp_time_course.trial_identifier = temp_run_identifier_object
                    # Data in seconds, data required to be in hours
                    # print(data[0][1:])
                    temp_time_course.time_vector = np.array(np.divide(data[0][1:], 3600))

                    temp_time_course.data_vector = np.array(row[1:])
                    self.titer_dict[temp_time_course.getTimeCourseID()] = copy.copy(temp_time_course)

            tf = time.time()
            print("Parsed %i timeCourseObjects in %0.3fs\n" % (len(self.titer_dict), tf - t0))

            self.parseTiterObjectCollection(self.titer_dict)

        if dataFormat == 'NV_titers':
            substrate_name = 'Glucose'
            titerDataSheetName = "titers"

            if 'titers' not in data.keys():
                raise Exception("No sheet named 'titers' found")

            ######## Initialize variables
            analyte_nameColumn = dict()
            for i in range(1, len(data[titerDataSheetName][2])):
                analyte_nameColumn[data[titerDataSheetName][2][i]] = i

            tempTimePointCollection = dict()
            for names in analyte_nameColumn:
                tempTimePointCollection[names] = []

            timePointCollection = []
            skipped_lines = 0
            # timepoint_list = []

            ######## Parse the titer data into single experiment object list
            ### NOTE: THIS PARSER IS NOT GENERIC AND MUST BE MODIFIED FOR YOUR SPECIFIC INPUT TYPE ###
            for i in range(4, len(data['titers'])):
                if type("asdf") == type(data['titers'][i][0]):  # Check if the data is a string
                    tempParsedIdentifier = data['titers'][i][0].split(',')  # Parse the string using comma delimiter
                    if len(tempParsedIdentifier) >= 3:  # Ensure corect number of identifiers TODO make this general
                        temptrial_identifierObject = TrialIdentifier()
                        tempParsedstrain_identifier = tempParsedIdentifier[0].split("+")
                        temptrial_identifierObject.strain_id = tempParsedstrain_identifier[0]
                        temptrial_identifierObject.id_1 = tempParsedstrain_identifier[1]
                        # temptrial_identifierObject.id_2 = tempParsedIdentifier[2]
                        tempParsedReplicate = tempParsedIdentifier[1].split('=')
                        temptrial_identifierObject.replicate_id = int(tempParsedReplicate[1])  # tempParsedIdentifier[1]
                        tempParsedTime = tempParsedIdentifier[2].split('=')
                        temptrial_identifierObject.t = float(tempParsedTime[1])  # tempParsedIdentifier[2]

                        for key in tempTimePointCollection:
                            temptrial_identifierObject.analyte_name = key
                            if key == 'Glucose':
                                temptrial_identifierObject.analyte_type = 'substrate'
                            else:
                                temptrial_identifierObject.analyte_type = 'product'
                            self.timepoint_list.append(
                                TimePoint(copy.copy(temptrial_identifierObject), key, temptrial_identifierObject.t,
                                          data['titers'][i][analyte_nameColumn[key]]))

                    else:
                        skipped_lines += 1
                else:
                    skipped_lines += 1
            tf = time.time()
            print("Parsed %i timeCourseObjects in %0.3fs\n" % (len(self.timepoint_list), tf - t0))
            print("Number of lines skipped: ", skipped_lines)
            self.parseTimePointCollection(self.timepoint_list, stage_indices=stage_indices)

        if dataFormat == 'NV_titers0.2':
            substrate_name = 'Glucose'
            titerDataSheetName = "titers"

            if 'titers' not in data.keys():
                raise Exception("No sheet named 'titers' found")

            # Initialize variables
            analyte_nameColumn = dict()
            for i in range(1, len(data[titerDataSheetName][2])):
                analyte_nameColumn[data[titerDataSheetName][2][i]] = i

            tempTimePointCollection = dict()
            for names in analyte_nameColumn:
                tempTimePointCollection[names] = []

            timePointCollection = []
            skipped_lines = 0
            # timepoint_list = []

            # Parse the titer data into single experiment object list
            for i in range(4, len(data['titers'])):
                if type("asdf") == type(data['titers'][i][0]):  # Check if the data is a string
                    temp_run_identifier_object = TrialIdentifier()
                    temp_run_identifier_object.parse_trial_identifier_from_csv(data['titers'][i][0])

                    tempParsedIdentifier = data['titers'][i][0].split(',')  # Parse the string using comma delimiter

                    temp_run_identifier_object.t = 15.  # tempParsedIdentifier[2]

                    for key in tempTimePointCollection:
                        temp_run_identifier_object.analyte_name = key
                        if key == 'Glucose':
                            temp_run_identifier_object.analyte_type = 'substrate'
                            self.timepoint_list.append(TimePoint(copy.copy(temp_run_identifier_object), key, 0, 12))
                        else:
                            temp_run_identifier_object.analyte_type = 'product'
                            self.timepoint_list.append(TimePoint(copy.copy(temp_run_identifier_object), key, 0, 0))
                        self.timepoint_list.append(
                            TimePoint(copy.copy(temp_run_identifier_object), key, temp_run_identifier_object.t,
                                      data['titers'][i][analyte_nameColumn[key]]))


                    else:
                        skipped_lines += 1
                else:
                    skipped_lines += 1




            tf = time.time()
            print("Parsed %i timeCourseObjects in %0.3fs\n" % (len(self.timepoint_list), tf - t0))
            print("Number of lines skipped: ", skipped_lines)
            self.parseTimePointCollection(self.timepoint_list)

        if dataFormat == 'KN_titers':
            # Parameters
            row_with_titer_names = 0
            first_data_row = 1

            substrate_name = 'glucose'
            titerDataSheetName = "titers"

            if fileName is not None:
                if 'titers' not in data.keys():
                    raise Exception("No sheet named 'titers' found")
            elif data is not None:
                data = {titerDataSheetName: data}
            else:
                raise Exception('No fileName or data')

            # Initialize variables
            analyte_nameColumn = dict()
            for i in range(1, len(data[titerDataSheetName][row_with_titer_names])):
                analyte_nameColumn[data[titerDataSheetName][row_with_titer_names][i]] = i

            tempTimePointCollection = dict()
            for names in analyte_nameColumn:
                tempTimePointCollection[names] = []

            skipped_lines = 0
            for i in range(first_data_row, len(data['titers'])):
                if type(data['titers'][i][0]) is str:
                    temp_run_identifier_object = TrialIdentifier()
                    temp_run_identifier_object.parse_trial_identifier_from_csv(data['titers'][i][0])

                    for key in tempTimePointCollection:
                        temp_run_identifier_object.analyte_name = key
                        if key == substrate_name:
                            temp_run_identifier_object.analyte_type = 'substrate'
                        else:
                            temp_run_identifier_object.analyte_type = 'product'

                        # Remove these time points
                        if temp_run_identifier_object.time not in [12, 72, 84]:
                            self.timepoint_list.append(
                                TimePoint(copy.copy(temp_run_identifier_object), key, temp_run_identifier_object.time,
                                          data['titers'][i][analyte_nameColumn[key]]))

                else:
                    skipped_lines += 1
            tf = time.time()
            print("Parsed %i timeCourseObjects in %0.3fs\n" % (len(self.timepoint_list), tf - t0))
            print("Number of lines skipped: ", skipped_lines)
            self.parseTimePointCollection(self.timepoint_list)

        if dataFormat == 'default_titers':
            # Parameters
            row_with_titer_names = 0
            row_with_titer_types = 1
            first_data_row = 2

            titerDataSheetName = "titers"

            if fileName is not None:
                from collections import OrderedDict
                if type(data) in [dict, type(OrderedDict())]:
                    if 'titers' not in data.keys():  # TODO data has no keys if there is only one sheet
                        raise Exception("No sheet named 'titers' found")
                else:
                    data = {titerDataSheetName: data}
            elif data is not None:
                data = {titerDataSheetName: data}
            else:
                raise Exception('No fileName or data')

            # Initialize variables
            analyte_nameColumn = dict()
            titer_type = dict()
            for i in range(1, len(data[titerDataSheetName][row_with_titer_names])):
                analyte_nameColumn[data[titerDataSheetName][row_with_titer_names][i]] = i
                titer_type[data[titerDataSheetName][row_with_titer_names][i]] = \
                    data[titerDataSheetName][row_with_titer_types][i]
            # print(titer_type)
            # Initialize a timepoint_collection for each titer type (column)
            tempTimePointCollection = dict()
            for names in analyte_nameColumn:
                tempTimePointCollection[names] = []

            skipped_lines = 0
            for i in range(first_data_row, len(data['titers'])):
                # print(data['titers'][i])
                if type(data['titers'][i][0]) is str:
                    temp_run_identifier_object = TrialIdentifier()
                    temp_run_identifier_object.parse_trial_identifier_from_csv(data['titers'][i][0])

                    # temp_run_identifier_object.strain_id = strain_rename_dict[temp_run_identifier_object.strain_id]

                    for key in tempTimePointCollection:
                        temp_run_identifier_object.analyte_name = key
                        temp_run_identifier_object.analyte_type = titer_type[key]
                        # if key == substrate_name:
                        #     temp_run_identifier_object.titerType = 'substrate'
                        # else:
                        #     temp_run_identifier_object.titerType = 'product'

                        # Remove these time points
                        # if temp_run_identifier_object.time not in [12, 72, 84]:
                            # print(temp_run_identifier_object.time,' ',data['titers'][i][analyte_nameColumn[key]])
                        if data['titers'][i][analyte_nameColumn[key]] == 'nan':
                            data['titers'][i][analyte_nameColumn[key]] = np.nan
                        self.timepoint_list.append(
                            TimePoint(copy.copy(temp_run_identifier_object), key,
                                      temp_run_identifier_object.time,
                                      data['titers'][i][analyte_nameColumn[key]]))

                else:
                    skipped_lines += 1
            tf = time.time()
            print("Parsed %i timeCourseObjects in %0.3fs\n" % (len(self.timepoint_list), tf - t0))
            print("Number of lines skipped: ", skipped_lines)
            self.parseTimePointCollection(self.timepoint_list)

        # This is the new way all parsers should be defined and called
        parser_case_dict = {'spectromax_OD':parsers.spectromax_OD}
        if dataFormat in parser_case_dict.keys():   parser_case_dict[dataFormat](self,data)



    def parseTimePointCollection(self, timePointList, stage_indices=None):
        print('Parsing time point list...')
        t0 = time.time()
        for timePoint in timePointList:
            flag = 0
            if timePoint.get_unique_timepoint_id() in self.titer_dict:
                self.titer_dict[timePoint.get_unique_timepoint_id()].add_timepoint(timePoint)
            else:
                self.titer_dict[timePoint.get_unique_timepoint_id()] = TimeCourse()
                self.titer_dict[timePoint.get_unique_timepoint_id()].add_timepoint(timePoint)
        tf = time.time()
        print("Parsed %i titer objects in %0.1fs\n" % (len(self.titer_dict), (tf - t0)))
        self.parseTiterObjectCollection(self.titer_dict, stage_indices=stage_indices)

    def parse_titers(self, titer_list):
        print('Parsing titer object list...')
        t0 = time.time()
        uniques = list(set([titer.getTimeCourseID() for titer in titer_list]))

        single_trial_list = []
        for unique in uniques:
            single_trial = SingleTrial()
            for titer in titer_list:
                if titer.getTimeCourseID() == unique:
                    single_trial.add_titer(titer)
            single_trial_list.append(single_trial)

        tf = time.time()
        print("Parsed %i titer objects in %0.1fms\n" % (len(single_trial_list), (tf - t0) * 1000))

        self.parse_single_trial_list(single_trial_list)

    def parse_single_trial_list(self, single_trial_list):
        uniques = list(set([single_trial.get_unique_replicate_id() for single_trial in single_trial_list]))

        replicate_trial_list = []
        for unique in uniques:
            replicate_trial = ReplicateTrial()
            for single_trial in single_trial_list:
                if single_trial.get_unique_replicate_id() == unique:
                    replicate_trial.add_replicate(single_trial)
                    replicate_trial_list.append(replicate_trial)

        self.replicate_experiment_dict = dict()
        for replicate_trial in replicate_trial_list:
            self.add_replicate_trial(replicate_trial)

    def parseTiterObjectCollection(self, titerObjectDict, stage_indices=None):
        print('Parsing titer object list...')
        t0 = time.time()
        for titerObjectDictKey in titerObjectDict:
            if titerObjectDict[titerObjectDictKey].getTimeCourseID() in self.single_experiment_dict:
                self.single_experiment_dict[titerObjectDict[titerObjectDictKey].getTimeCourseID()].add_titer(
                    titerObjectDict[titerObjectDictKey])
            else:
                self.single_experiment_dict[titerObjectDict[titerObjectDictKey].getTimeCourseID()] = SingleTrial()
                self.single_experiment_dict[titerObjectDict[titerObjectDictKey].getTimeCourseID()].add_titer(
                    titerObjectDict[titerObjectDictKey])
        tf = time.time()
        print("Parsed %i single trials in %0.1fms\n" % (len(self.single_experiment_dict), (tf - t0) * 1000))
        self.parseSingleExperimentObjectList(self.single_experiment_dict)

    def parseSingleExperimentObjectList(self, singleExperimentObjectList):
        print('Parsing single experiment object list...')
        t0 = time.time()
        for key in singleExperimentObjectList:
            flag = 0
            for key2 in self.replicate_experiment_dict:
                if key2 == singleExperimentObjectList[key].get_unique_replicate_id():
                    self.replicate_experiment_dict[key2].add_replicate(singleExperimentObjectList[key])
                    flag = 1
                    break
            if flag == 0:
                self.replicate_experiment_dict[
                    singleExperimentObjectList[key].get_unique_replicate_id()] = ReplicateTrial()
                self.replicate_experiment_dict[
                    singleExperimentObjectList[key].get_unique_replicate_id()].add_replicate(
                    singleExperimentObjectList[key])
        tf = time.time()
        print("Parsed %i replicates in %0.1fs\n" % (len(self.replicate_experiment_dict), (tf - t0)))

    def add_replicate_trial(self, replicateTrial):
        """
        Add a :class:`~ReplicateTrial` to the experiment.

        Parameters
        ----------
        replicateTrial : :class:`~ReplicateTrial`
        """
        self.replicate_experiment_dict[replicateTrial.single_trial_list[0].get_unique_replicate_id()] = replicateTrial

    def pickle(self, fileName):
        """
        Pickle experiment. Not commonly used since 2016/06/14
        """
        pickle.dump([self.timepoint_list, self.titer_dict, self.single_experiment_dict,
                     self.replicate_experiment_dict], open(fileName, 'wb'))

    def unpickle(self, fileName):
        """
        Unpickle pickled experiments. Not commonly used since 2016/06/14
        """
        t0 = time.time()
        with open(fileName, 'rb') as data:
            self.timepoint_list, self.titer_dict, self.single_experiment_dict, self.replicate_experiment_dict = pickle.load(
                data)
        print('Read data from %s in %0.3fs' % (fileName, time.time() - t0))

    def printGenericTimeCourse(self, figHandle=[], strainsToPlot=[], titersToPlot=[], removePointFraction=1,
                               shadeErrorRegion=False, showGrowthRates=True, plotCurveFit=True, output_type='iPython',
                               **kwargs):
        """
        Wrapper for FermAT.printGenericTimeCourse_plotly
        """
        if strainsToPlot == []:
            strainsToPlot = self.get_strains()

        # Plot all product titers if none specified TODO: Add an option to plot OD as well
        if titersToPlot == []:
            titersToPlot = self.get_titers()

        replicateTrialList = [self.replicate_experiment_dict[key] for key in strainsToPlot]

        from FermAT import printGenericTimeCourse_plotly
        printGenericTimeCourse_plotly(replicateTrialList=replicateTrialList, titersToPlot=titersToPlot,
                                      output_type=output_type, **kwargs)



        # if figHandle == []:
        #     figHandle = plt.figure(figsize=(12, 8))
        #
        # figHandle.set_facecolor('w')
        #

        #
        # # Determine optimal figure size
        # if len(titersToPlot) == 1:
        #     figureSize = (12, 6)
        # if len(titersToPlot) > 1:
        #     figureSize = (12, 3.5)
        # if len(titersToPlot) > 4:
        #     figureSize = (12, 7)
        #
        # if plotCurveFit == True:
        #     plotSymbol = 'o'
        # else:
        #     plotSymbol = 'o-'
        #
        # figHandle  # .set_size_inches(figureSize, forward=True)
        # # plt.figure(figsize=figureSize)
        # plt.clf()
        #
        # colors = plt.get_cmap(self.colorMap)(np.linspace(0, 1, len(strainsToPlot)))
        #
        # pltNum = 0
        # print(titersToPlot)
        # for product in titersToPlot:
        #     pltNum += 1
        #
        #     # Choose the subplot layout
        #     if len(titersToPlot) == 1:
        #         ax = plt.subplot(111)
        #     elif len(titersToPlot) < 5:
        #         ax = plt.subplot(1, len(titersToPlot), pltNum)
        #     elif len(titersToPlot) < 9:
        #         ax = plt.subplot(2, (len(titersToPlot) + 1) / 2, pltNum)
        #     else:
        #         raise Exception("Unimplemented Functionality")
        #
        #     # Set some axis aesthetics
        #     ax.spines["top"].set_visible(False)
        #     ax.spines["right"].set_visible(False)
        #
        #     colorIndex = 0
        #     handle = dict()
        #     xlabel = 'Time (hours)'
        #     for key in strainsToPlot:
        #         xData = self.replicate_experiment_dict[key].t
        #         if product == 'OD' or product == self.replicate_experiment_dict[key].avg.titer_dict[product].trial_identifier.analyte_name:
        #             product = self.replicate_experiment_dict[key].avg.titer_dict[product].trial_identifier.analyte_name
        #             scaledTime = self.replicate_experiment_dict[key].t
        #             # Plot the fit curve
        #             if plotCurveFit == True:
        #                 handle[key] = plt.plot(np.linspace(min(scaledTime), max(scaledTime), 50),
        #                                        self.replicate_experiment_dict[key].avg.titer_dict[
        #                                            product].data_curve_fit(
        #                                            np.linspace(min(self.replicate_experiment_dict[key].t),
        #                                                        max(self.replicate_experiment_dict[key].t), 50)),
        #                                        '-', lw=1.5, color=colors[colorIndex])
        #             # Plot the data
        #             print(product)
        #             print(scaledTime[::removePointFraction])
        #             print()
        #             handle[key] = plt.errorbar(scaledTime[::removePointFraction],
        #                                        self.replicate_experiment_dict[key].avg.titer_dict[
        #                                            product].data_vector[::removePointFraction],
        #                                        self.replicate_experiment_dict[key].std.titer_dict[
        #                                            product].data_vector[::removePointFraction],
        #                                        lw=2.5, elinewidth=1, capsize=2, fmt=plotSymbol, markersize=5,
        #                                        color=colors[colorIndex])
        #             # Fill in the error bar range
        #             # if shadeErrorRegion==True:
        #             #     plt.fill_between(scaledTime,self.replicate_experiment_dict[key].avg.OD.data_vector+self.replicate_experiment_dict[key].std.OD.data_vector,
        #             #                      self.replicate_experiment_dict[key].avg.OD.data_vector-self.replicate_experiment_dict[key].std.OD.data_vector,
        #             #                      facecolor=colors[colorIndex],alpha=0.1)
        #             # # Add growth rates at end of curve
        #             # if showGrowthRates==True:
        #             #     plt.text(scaledTime[-1]+0.5,
        #             #              self.replicate_experiment_dict[key].avg.OD.data_curve_fit(np.linspace(min(self.replicate_experiment_dict[key].t),max(self.replicate_experiment_dict[key].t),50))[-1],
        #             #              '$\mu$ = '+'{:.2f}'.format(self.replicate_experiment_dict[key].avg.OD.rate[1]) + ' $\pm$ ' + '{:.2f}'.format(self.replicate_experiment_dict[key].std.OD.rate[1])+', n='+str(len(self.replicate_experiment_dict[key].replicate_ids)-len(self.replicate_experiment_dict[key].bad_replicates)),
        #             #              verticalalignment='center')
        #             # ylabel = 'OD$_{600}$'
        #         else:
        #             scaledTime = self.replicate_experiment_dict[key].t
        #
        #             # handle[key] = plt.plot(np.linspace(min(scaledTime),max(scaledTime),50),
        #             #                         self.replicate_experiment_dict[key].avg.products[product].data_curve_fit(np.linspace(min(self.replicate_experiment_dict[key].t),max(self.replicate_experiment_dict[key].t),50)),
        #             #                        '-',lw=0.5,color=colors[colorIndex])
        #
        #             handle[key] = plt.errorbar(self.replicate_experiment_dict[key].t[::removePointFraction],
        #                                        self.replicate_experiment_dict[key].avg.titer_dict[
        #                                            product].data_vector[::removePointFraction],
        #                                        self.replicate_experiment_dict[key].std.titer_dict[
        #                                            product].data_vector[::removePointFraction], lw=2.5, elinewidth=1,
        #                                        capsize=2, fmt='o-', color=colors[colorIndex])
        #             ylabel = product + " AnalyteData (g/L)"
        #
        #         colorIndex += 1
        #         # plt.show()
        #     plt.xlabel(xlabel)
        #     # plt.ylabel(ylabel)
        #     ymin, ymax = plt.ylim()
        #     xmin, xmax = plt.xlim()
        #     plt.xlim([0, xmax * 1.2])
        #     plt.ylim([0, ymax])
        # # plt.style.use('ggplot')
        # plt.tight_layout()
        # plt.tick_params(right="off", top="off")
        # # plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0, frameon=False)
        # plt.subplots_adjust(right=0.7)
        #
        # if len(titersToPlot) == 1:
        #     plt.legend([handle[key] for key in handle], [key for key in handle], bbox_to_anchor=(1.05, 0.5), loc=6,
        #                borderaxespad=0, frameon=False)
        #     plt.subplots_adjust(right=0.7)
        # elif len(titersToPlot) < 5:
        #     plt.legend([handle[key] for key in handle], [key for key in handle], bbox_to_anchor=(1.05, 0.5), loc=6,
        #                borderaxespad=0, frameon=False)
        #     plt.subplots_adjust(right=0.75)
        # else:
        #     plt.legend([handle[key] for key in handle], [key for key in handle], bbox_to_anchor=(1.05, 1.1), loc=6,
        #                borderaxespad=0, frameon=False)
        #     plt.subplots_adjust(right=0.75)
        #
        #     # Save the figure
        #     # plt.savefig(os.path.join(os.path.dirname(__file__),'Figures/'+time.strftime('%y')+'.'+time.strftime('%m')+'.'+time.strftime('%d')+" H"+time.strftime('%H')+'-M'+time.strftime('%M')+'-S'+time.strftime('%S')+'.png'))
        #     # plt.show()

    def printGrowthRateBarChart(self, figHandle=[], strainsToPlot=[], sortBy='id_1'):
        """
        MPL plotting function, deprecated since 2016/06/14 due to switch to plotly
        """
        if figHandle == []:
            figHandle = plt.figure(figsize=(9, 5))

        if strainsToPlot == []:
            strainsToPlot = [key for key in self.replicate_experiment_dict]

        # Sort the strains to plot to HELP ensure that things are in the same order
        # TODO should find a better way to ensure this is the case
        strainsToPlot.sort()

        # Clear the plot and set some aesthetics
        plt.cla()
        ax = plt.subplot(111)
        figHandle.set_facecolor('w')
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Find all the unique identifier based on which identifier to 'sortBy'
        uniques = list(
            set([getattr(self.replicate_experiment_dict[key].trial_identifier, sortBy) for key in strainsToPlot]))
        uniques.sort()

        # Find max number of samples (in case they all aren't the same)
        maxSamples = 0
        for unique in uniques:
            if len([self.replicate_experiment_dict[key].avg.OD.rate[1] for key in strainsToPlot if
                    getattr(self.replicate_experiment_dict[key].trial_identifier, sortBy) == unique]) > maxSamples:
                maxSamples = len([self.replicate_experiment_dict[key].avg.OD.rate[1] for key in strainsToPlot if
                                  getattr(self.replicate_experiment_dict[key].trial_identifier, sortBy) == unique])
                maxIndex = unique

        barWidth = 0.9 / len(uniques)
        index = np.arange(maxSamples)
        colors = plt.get_cmap('Set2')(np.linspace(0, 1.0, len(uniques)))

        i = 0
        handle = dict()
        for unique in uniques:
            handle[unique] = plt.bar(index[0:len(
                [self.replicate_experiment_dict[key].avg.OD.rate[1] for key in strainsToPlot if
                 getattr(self.replicate_experiment_dict[key].trial_identifier, sortBy) == unique])],
                                     [self.replicate_experiment_dict[key].avg.OD.rate[1] for key in strainsToPlot if
                                      getattr(self.replicate_experiment_dict[key].trial_identifier, sortBy) == unique],
                                     barWidth, yerr=[self.replicate_experiment_dict[key].std.OD.rate[1] for key in
                                                     strainsToPlot if
                                                     getattr(self.replicate_experiment_dict[key].trial_identifier,
                                                             sortBy) == unique],
                                     color=colors[i], ecolor='k', capsize=5, error_kw=dict(elinewidth=1, capthick=1))
            i += 1
            index = index + barWidth

        ax.yaxis.set_ticks_position('left')
        ax.xaxis.set_ticks_position('bottom')
        plt.ylabel('Growth Rate ($\mu$, h$^{-1}$)')
        xticklabel = ''
        for attribute in ['strain_id', 'id_1', 'id_2']:
            if attribute != sortBy:
                xticklabel = xticklabel + attribute

        if 'strain_id' == sortBy:
            tempticks = [self.replicate_experiment_dict[key].trial_identifier.id_1 + '+' +
                         self.replicate_experiment_dict[key].trial_identifier.id_2 for key in strainsToPlot
                         if getattr(self.replicate_experiment_dict[key].trial_identifier, sortBy) == maxIndex]
        if 'id_1' == sortBy:
            tempticks = [self.replicate_experiment_dict[key].trial_identifier.strain_id + '+' +
                         self.replicate_experiment_dict[key].trial_identifier.id_2 for key in strainsToPlot
                         if getattr(self.replicate_experiment_dict[key].trial_identifier, sortBy) == maxIndex]
        if 'id_2' == sortBy:
            tempticks = [self.replicate_experiment_dict[key].trial_identifier.strain_id + '+' +
                         self.replicate_experiment_dict[key].trial_identifier.id_1 for key in strainsToPlot
                         if getattr(self.replicate_experiment_dict[key].trial_identifier, sortBy) == maxIndex]
        tempticks.sort()

        plt.xticks(index - 0.4, tempticks, rotation='45', ha='right', va='top')
        plt.tight_layout()
        plt.subplots_adjust(right=0.75)
        # print([handle[key][0][0] for key in handle])
        plt.legend([handle[key][0] for key in uniques], uniques, bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0)
        # ax.hold(False)

        return figHandle

    def printEndPointYield(self, figHandle=[], strainsToPlot=[], titersToPlot=[], sortBy='id_2', withLegend=2):
        """
        MPL plotting function, deprecated since 2016/06/14 due to switch to plotly
        """
        if figHandle == []:
            figHandle = plt.figure(figsize=(9, 5))

        if strainsToPlot == []:
            strainsToPlot = self.get_strains()

        if titersToPlot == []:
            titersToPlot = self.get_titers()

        # Clear the plot and set some aesthetics
        plt.cla()
        ax = plt.subplot(111)
        figHandle.set_facecolor('w')
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # uniques = list(set([getattr(self.replicate_experiment_dict[key].TrialIdentifier,sortBy) for key in strainsToPlot]))
        # uniques.sort()
        #
        # # Find max number of samples (in case they all aren't the same)
        # maxSamples = 0
        # for unique in uniques:
        #     if len([self.replicate_experiment_dict[key].avg.OD.rate[1] for key in strainsToPlot if getattr(self.replicate_experiment_dict[key].TrialIdentifier,sortBy) == unique]) > maxSamples:
        #         maxSamples = len([self.replicate_experiment_dict[key].avg.OD.rate[1] for key in strainsToPlot if getattr(self.replicate_experiment_dict[key].TrialIdentifier,sortBy) == unique])
        #         maxIndex = unique

        replicateExperimentObjectList = self.replicate_experiment_dict
        handle = dict()
        colors = plt.get_cmap('Set2')(np.linspace(0, 1.0, len(strainsToPlot)))

        barWidth = 0.6
        pltNum = 0

        if withLegend == 2:
            # # First determine which items to separate plot by (titer/OD, strain, id1, id2)
            # # TODO implement this
            #
            # # Then determine which items to group the plot by



            for product in titersToPlot:
                uniques = list(set(
                    [getattr(self.replicate_experiment_dict[key].trial_identifier, sortBy) for key in strainsToPlot]))
                uniques.sort()

                # Find max number of samples (in case they all aren't the same)
                maxSamples = 0
                for unique in uniques:
                    if len([self.replicate_experiment_dict[key].avg.products[product] for key in strainsToPlot if
                            getattr(self.replicate_experiment_dict[key].trial_identifier,
                                    sortBy) == unique]) > maxSamples:
                        # if len([self.replicate_experiment_dict[key].avg.products[prodKey] for prodkey in self.replicate_experiment_dict[key] for key in strainsToPlot if getattr(self.replicate_experiment_dict[key].TrialIdentifier,sortBy) == unique]) > maxSamples:
                        maxSamples = len(
                            [self.replicate_experiment_dict[key].avg.products[product] for key in strainsToPlot if
                             getattr(self.replicate_experiment_dict[key].trial_identifier, sortBy) == unique])
                        maxIndex = unique

                # Create empty arrays to store data
                endPointTiterAvg = []
                endPointTiterStd = []
                endPointTiterLabel = []

                # Choose plot number
                pltNum += 1
                ax = plt.subplot(1, len(titersToPlot), pltNum)

                # Initial variables and choose plotting locations of bars
                location = 0

                # Prepare data for plotting
                for key in strainsToPlot:
                    if getattr(self.replicate_experiment_dict[key].trial_identifier, sortBy) == unique:
                        endPointTiterLabel.append(key)
                        endPointTiterAvg.append(replicateExperimentObjectList[key].avg.yields[product][-1])
                        endPointTiterStd.append(replicateExperimentObjectList[key].std.yields[product][-1])

                barWidth = 0.9 / len(uniques)
                index = np.arange(maxSamples)
                colors = plt.get_cmap('Set2')(np.linspace(0, 1.0, len(uniques)))

                i = 0
                for unique in uniques:
                    print([self.replicate_experiment_dict[key].avg.yields[product][-1] for key in strainsToPlot if
                           getattr(self.replicate_experiment_dict[key].trial_identifier, sortBy) == unique])
                    print(len(
                        [self.replicate_experiment_dict[key].avg.yields[product][-1] for key in strainsToPlot if
                         getattr(self.replicate_experiment_dict[key].trial_identifier, sortBy) == unique]))
                    print(
                        [getattr(self.replicate_experiment_dict[key].trial_identifier, sortBy) for key in strainsToPlot
                         if getattr(self.replicate_experiment_dict[key].trial_identifier, sortBy) == unique])
                    print()
                    handle[unique] = plt.bar(index[0:len(
                        [self.replicate_experiment_dict[key].avg.products[product] for key in strainsToPlot if
                         getattr(self.replicate_experiment_dict[key].trial_identifier, sortBy) == unique])],
                                             [self.replicate_experiment_dict[key].avg.yields[product][-1] for key in
                                              strainsToPlot if
                                              getattr(self.replicate_experiment_dict[key].trial_identifier,
                                                      sortBy) == unique],
                                             barWidth,
                                             yerr=[self.replicate_experiment_dict[key].std.yields[product][-1] for
                                                   key in strainsToPlot if
                                                   getattr(self.replicate_experiment_dict[key].trial_identifier,
                                                           sortBy) == unique],
                                             color=colors[i], ecolor='k', capsize=5,
                                             error_kw=dict(elinewidth=1, capthick=1)
                                             )
                    index = index + barWidth
                    i += 1

                plt.ylabel(product + " Yield (g/g)")
                ymin, ymax = plt.ylim()
                plt.ylim([0, ymax])

                endPointTiterLabel.sort()

                xticklabel = ''
                for attribute in ['strain_id', 'id_1', 'id_2']:
                    if attribute != sortBy:
                        xticklabel = xticklabel + attribute

                if 'strain_id' == sortBy:
                    tempticks = [self.replicate_experiment_dict[key].trial_identifier.id_1 + '+' +
                                 self.replicate_experiment_dict[key].trial_identifier.id_2 for key in
                                 strainsToPlot
                                 if getattr(self.replicate_experiment_dict[key].trial_identifier, sortBy) == maxIndex]
                if 'id_1' == sortBy:
                    tempticks = [self.replicate_experiment_dict[key].trial_identifier.strain_id + '+' +
                                 self.replicate_experiment_dict[key].trial_identifier.id_2 for key in
                                 strainsToPlot
                                 if getattr(self.replicate_experiment_dict[key].trial_identifier, sortBy) == maxIndex]
                if 'id_2' == sortBy:
                    tempticks = [self.replicate_experiment_dict[key].trial_identifier.strain_id + '+' +
                                 self.replicate_experiment_dict[key].trial_identifier.id_1 for key in
                                 strainsToPlot
                                 if getattr(self.replicate_experiment_dict[key].trial_identifier, sortBy) == maxIndex]
                tempticks.sort()

                plt.xticks(index - 0.4, tempticks, rotation='45', ha='right', va='top')

                ax.yaxis.set_ticks_position('left')
                ax.xaxis.set_ticks_position('bottom')
            figManager = plt.get_current_fig_manager()
            figManager.window.showMaximized()
            plt.tight_layout()
            plt.subplots_adjust(right=0.875)
            plt.legend([handle[key][0] for key in uniques], uniques, bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0)

        if withLegend == 0:
            plt.figure(figsize=(6, 3))
            for product in titersToPlot:
                endPointTiterAvg = []
                endPointTiterStd = []
                endPointTiterLabel = []
                pltNum += 1
                # ax = plt.subplot(0.8)
                ax = plt.subplot(1, len(
                    replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products), pltNum)
                ax.spines["top"].set_visible(False)
                # ax.spines["bottom"].set_visible(False)
                ax.spines["right"].set_visible(False)
                # ax.spines["left"].set_visible(False)
                location = 0
                index = np.arange(len(strainsToPlot))

                strainsToPlot.sort()

                for key in strainsToPlot:
                    endPointTiterLabel.append(key)
                    endPointTiterAvg.append(replicateExperimentObjectList[key].avg.yields[product][-1])
                    endPointTiterStd.append(replicateExperimentObjectList[key].std.yields[product][-1])

                handle[key] = plt.bar(index, endPointTiterAvg, barWidth, yerr=endPointTiterStd,
                                      color=plt.get_cmap('Set2')(0.25), ecolor='black', capsize=5,
                                      error_kw=dict(elinewidth=1, capthick=1))
                location += barWidth
                plt.xlabel("Time (hours)")
                plt.ylabel(product + " Yield (g/g)")
                ymin, ymax = plt.ylim()
                plt.ylim([0, ymax])
                plt.tight_layout()
                endPointTiterLabel.sort()
                plt.xticks(index + barWidth / 2, endPointTiterLabel, rotation='45', ha='right', va='top')
                ax.yaxis.set_ticks_position('left')
                ax.xaxis.set_ticks_position('bottom')

        if withLegend == 1:
            plt.figure(figsize=(6, 2))

            for product in replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products:
                endPointTiterAvg = []
                endPointTiterStd = []
                endPointTiterLabel = []
                pltNum += 1
                ax = plt.subplot(1, len(
                    replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products), pltNum)
                ax.spines["top"].set_visible(False)
                # ax.spines["bottom"].set_visible(False)
                ax.spines["right"].set_visible(False)
                # ax.spines["left"].set_visible(False)
                location = 0
                index = np.arange(len(strainsToPlot))

                for key in strainsToPlot:
                    endPointTiterLabel.append(key)
                    endPointTiterAvg.append(replicateExperimentObjectList[key].avg.yields[product][-1])
                    endPointTiterStd.append(replicateExperimentObjectList[key].std.yields[product][-1])

                barList = plt.bar(index, endPointTiterAvg, barWidth, yerr=endPointTiterStd, ecolor='k')
                count = 0
                for bar, count in zip(barList, range(len(strainsToPlot))):
                    bar.set_color(colors[count])
                location += barWidth
                plt.ylabel(product + " AnalyteData (g/L)")
                ymin, ymax = plt.ylim()
                plt.ylim([0, ymax])
                plt.tight_layout()
                plt.xticks([])
                ax.yaxis.set_ticks_position('left')
                ax.xaxis.set_ticks_position('bottom')
            plt.subplots_adjust(right=0.7)
            plt.legend(barList, strainsToPlot, bbox_to_anchor=(1.15, 0.5), loc=6, borderaxespad=0)

    def printYieldTimeCourse(self, strainsToPlot):
        """
        MPL plotting function, deprecated since 2016/06/14 due to switch to plotly
        """
        replicateExperimentObjectList = self.replicate_experiment_dict
        # You typically want your plot to be ~1.33x wider than tall. This plot is a rare
        # exception because of the number of lines being plotted on it.
        # Common sizes: (10, 7.5) and (12, 9)
        plt.figure(figsize=(12, 3))

        handle = dict()
        barWidth = 0.9 / len(strainsToPlot)
        # plt.hold(False)
        pltNum = 0
        colors = plt.get_cmap('Paired')(np.linspace(0, 1.0, len(strainsToPlot)))
        for product in replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products:
            pltNum += 1
            ax = plt.subplot(1, len(
                replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products) + 1, pltNum)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            location = 0
            colorIndex = 0
            for key in strainsToPlot:
                index = np.arange(len(replicateExperimentObjectList[key].t))
                handle[key] = plt.bar(index + location, replicateExperimentObjectList[key].avg.yields[product],
                                      barWidth, yerr=replicateExperimentObjectList[key].std.yields[product],
                                      color=colors[colorIndex], ecolor='k')
                plt.xticks(index + barWidth, replicateExperimentObjectList[key].t)
                location += barWidth
                colorIndex += 1
                # print(replicateExperimentObjectList[key].avg.products[product].rate)
                # handle[key] = plt.plot(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50),
                #                                    replicateExperimentObjectList[key].avg.products[product].data_curve_fit(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50)),'-',lw=2.5)
            plt.xlabel("Time (hours)")
            plt.ylabel(product + " Yield (g/g)")
            ymin, ymax = plt.ylim()
            plt.ylim([0, 1])
            plt.tight_layout()
        # plt.subplot(1,4,4)
        plt.legend([handle[key] for key in handle], [key for key in handle], bbox_to_anchor=(1.15, 0.5), loc=6,
                   borderaxespad=0)
        plt.subplots_adjust(right=1.05)

    def printAllReplicateTimeCourse(self, figHandle=[], strainToPlot=[]):

        if figHandle == []:
            figHandle = plt.figure(figsize=(9, 5))

        plt.clf()
        if len(strainToPlot) > 1:
            strainToPlot = self.get_strains()[0]
        for singleExperiment in self.replicate_experiment_dict[strainToPlot[0]].single_trial_list:
            plt.plot(singleExperiment.OD.time_vector, singleExperiment.OD.data_vector)
        plt.ylabel(singleExperiment.trial_identifier.get_unique_id_for_ReplicateTrial())
        # plt.tight_layout()
