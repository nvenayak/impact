import copy
import datetime
import time
import time as sys_time

import numpy as np

from openpyxl import load_workbook

from .core.AnalyteData import TimePoint
from .core.TrialIdentifier import TimeCourseIdentifier


def spectromax_OD(experiment, data, id_type='CSV'):
    from .core.settings import settings
    live_calculations = settings.live_calculations
    
    unparsed_identifiers = [[elem.value for elem in row] for row in data['identifiers']]
    raw_data = [[elem.value for elem in row] for row in data['data']]

    # The data starts at (3,2) and is in a 8x12 format
    timepoint_list = []

    # Parse identifiers (to prevent parsing at every time point)
    identifiers = []
    for i, row in enumerate(unparsed_identifiers):
        parsed_row = []
        for j, data in enumerate(row):
            if unparsed_identifiers[i][j] not in ['', 0, '0', None]:
                temp_trial_identifier = TimeCourseIdentifier()

                if id_type == 'CSV':
                    temp_trial_identifier.parse_trial_identifier_from_csv(unparsed_identifiers[i][j])
                elif id_type == 'traverse':
                    temp_trial_identifier.parse_identifier(unparsed_identifiers[i][j])

                parsed_row.append(temp_trial_identifier)
            else:
                parsed_row.append(None)
        identifiers.append(parsed_row)

    for start_row_index in range(3, len(raw_data), 9):
        # print(start_row_index)
        # Parse the time point out first
        # print(raw_data[start_row_index][0])

        if raw_data[start_row_index][0] != '~End':
            if isinstance(raw_data[start_row_index][0],datetime.datetime):
                raise Exception("Imported a datetime object, make sure to set all cells to 'TEXT' if importing"
                                " from excel")
            parsed_time = raw_data[start_row_index][0].split(':')

            # Convert the Spectromax format to raw hours
            if len(parsed_time) > 2:
                time = int(parsed_time[0]) * 3600 + int(parsed_time[1]) * 60 + int(parsed_time[2])
            else:
                time = int(parsed_time[0]) * 60 + int(parsed_time[1])

            time /= 3600  # convert to hours

            # Define the data for a single plate, single timepoint
            plate_data = [row[2:14] for row in raw_data[start_row_index:start_row_index+8]]
            # print(plate_data)

            # Load the data point by point
            for i, row in enumerate(plate_data):
                for j, data in enumerate(row):
                    # Skip wells where no identifier is listed or no data present
                    if identifiers[i][j] is not None \
                            and data not in [None,'']:
                        # temp_trial_identifier = TimeCourseIdentifier()
                        #
                        # if id_type == 'CSV':
                        #     temp_trial_identifier.parse_trial_identifier_from_csv(identifiers[i][j])
                        # elif id_type == 'traverse':
                        #     temp_trial_identifier.parse_identifier(identifiers[i][j])
                        temp_trial_identifier = identifiers[i][j]
                        temp_trial_identifier.analyte_type = 'biomass'
                        temp_trial_identifier.analyte_name = 'OD600'
                        try:
                            # print('gooddata:', data)
                            temp_timepoint = TimePoint(temp_trial_identifier, time, float(data))
                        except Exception as e:
                            # print('baddata:',data)
                            print(plate_data)
                            raise Exception(e)
                        timepoint_list.append(temp_timepoint)
                    # else:
                    #     print('Skipped time point')
        else:
            break

    experiment.parse_time_point_dict(timepoint_list)

    if live_calculations:   experiment.calculate()


def spectromax_OD_triplicate(experiment, data, id_type='CSV'):
    from .core.settings import settings
    live_calculations = settings.live_calculations

    # This should be an ordered dict if imported from py_xlsx
    # assert isinstance(data, OrderedDict)

    identifiers = [[elem.value for elem in row] for row in data['identifiers']]
    raw_data = [[elem.value for elem in row] for row in data['data']]

    # The data starts at (3,2) and is in a 8x12 format
    timepoint_list = []

    for start_row_index in range(3, len(raw_data), 9):
        # print(start_row_index)
        # Parse the time point out first
        # print(raw_data[start_row_index][0])

        if raw_data[start_row_index][0] != '~End':
            if isinstance(raw_data[start_row_index][0], datetime.datetime):
                raise Exception("Imported a datetime object, make sure to set all cells to 'TEXT' if importing"
                                " from excel")
            parsed_time = raw_data[start_row_index][0].split(':')

            # Convert the Spectromax format to raw hours
            if len(parsed_time) > 2:
                time = int(parsed_time[0]) * 3600 + int(parsed_time[1]) * 60 + int(parsed_time[2])
            else:
                time = int(parsed_time[0]) * 60 + int(parsed_time[1])

            time /= 3600  # convert to hours
            # Define the data for each of the replicates
            replicate_plate_data = [[row[2:14] for row in raw_data[start_row_index:start_row_index + 8]],
                                    [row[15:27] for row in raw_data[start_row_index:start_row_index + 8]],
                                    [row[28:40] for row in raw_data[start_row_index:start_row_index + 8]]]
            # convert to strings to floats
            converted_data = []
            for plate_data in replicate_plate_data:
                converted_data.append([[float(data) if data is not None else 0. for data in row] for row in plate_data])

            # Calculate the average
            try:
                plate_data = np.mean(converted_data,axis=0)
            except Exception as e:
                print(converted_data)
                raise Exception(e)

            # Load the data point by point
            for i, row in enumerate(plate_data):
                for j, data in enumerate(row):
                    # Skip wells where no identifier is listed or no data present
                    if i<len(identifiers) and j<len(identifiers[0]) \
                            and identifiers[i][j] not in ['',0,'0',None] \
                            and data not in ['',None]:
                        temp_trial_identifier = TimeCourseIdentifier()

                        if id_type == 'CSV':
                            temp_trial_identifier.parse_trial_identifier_from_csv(identifiers[i][j])
                        elif id_type == 'traverse':
                            temp_trial_identifier.parse_identifier(identifiers[i][j])
                        temp_trial_identifier.analyte_type = 'biomass'
                        temp_trial_identifier.analyte_name = 'OD600'
                        temp_timepoint = TimePoint(temp_trial_identifier, time, float(data))

                        timepoint_list.append(temp_timepoint)
                        # else:
                        #     print('Skipped time point')
        else:
            break

    experiment.parse_time_point_dict(timepoint_list)

    if live_calculations:   experiment.calculate()


def HPLC_titer_parser(experiment, data, id_type='CSV'):
    t0 = sys_time.time()

    # Parameters
    row_with_titer_names = 0
    row_with_titer_types = 1
    first_data_row = 2
    titerDataSheetName = "titers"
    # if fileName is not None:
    #     from collections import OrderedDict
    #     if type(data) in [dict, type(OrderedDict())]:
    #         if 'titers' not in data.keys():  # TODO data has no keys if there is only one sheet
    #             raise Exception("No sheet named 'titers' found")
    #     else:
    #         data = {titerDataSheetName: data}
    # if data is not None:
    #     data = {titerDataSheetName: data}
    # else:
    #     raise Exception('No fileName or data')

    # Initialize variables
    analyte_nameColumn = dict()
    titer_type = dict()

    data = [[elem.value for elem in row] for row in data[titerDataSheetName]]

    for i in range(1, len(data[row_with_titer_names])):
        analyte_nameColumn[data[row_with_titer_names][i]] = i
        titer_type[data[row_with_titer_names][i]] = \
            data[row_with_titer_types][i]

    # Initialize a timepoint_collection for each titer type (column)
    tempTimePointCollection = dict()
    for names in analyte_nameColumn:
        tempTimePointCollection[names] = []
    skipped_lines = 0
    timepoint_list = []
    for i in range(first_data_row, len(data)):
        if type(data[i][0]) is str:
            for key in tempTimePointCollection:
                trial_identifier = TimeCourseIdentifier()
                trial_identifier.parse_trial_identifier_from_csv(data[i][0])

                if id_type == 'CSV':
                    trial_identifier.parse_trial_identifier_from_csv(data[i][0])
                elif id_type == 'traverse':
                    trial_identifier.parse_identifier(data[i][0])

                trial_identifier.analyte_name = key
                trial_identifier.analyte_type = titer_type[key]

                if data[i][analyte_nameColumn[key]] == 'nan':
                    data[i][analyte_nameColumn[key]] = np.nan
                timepoint_list.append(
                    TimePoint(trial_identifier=trial_identifier,
                              time=trial_identifier.time,
                              data=data[i][analyte_nameColumn[key]]))

        else:
            skipped_lines += 1
    tf = sys_time.time()
    print("Parsed %i timeCourseObjects in %0.3fs" % (len(timepoint_list), tf - t0), end='')
    print("...Number of lines skipped: ", skipped_lines)
    experiment.parse_time_point_dict(timepoint_list)
    # experiment.calculate()


def tecan_OD(experiment, data, fileName, t0):
    from .core.AnalyteData import TimeCourse

    t0 = sys_time.time()
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
        temp_run_identifier_object = TimeCourseIdentifier()
        if type(row[0]) is str:
            temp_run_identifier_object.parse_trial_identifier_from_csv(row[0])
            temp_run_identifier_object.analyte_name = 'OD600'
            temp_run_identifier_object.analyte_type = 'biomass'
            temp_time_course = TimeCourse()
            temp_time_course.trial_identifier = temp_run_identifier_object

            # Data in seconds, data required to be in hours
            temp_time_course.time_vector = np.array(np.divide(data[0][1:], 3600))

            temp_time_course.data_vector = np.array(row[1:])
            experiment.titer_dict[temp_time_course.trial_identifier.unique_single_trial()] = copy.copy(temp_time_course)
    tf = sys_time.time()
    print("Parsed %i timeCourseObjects in %0.3fs\n" % (len(experiment.titer_dict), tf - t0))
    experiment.parse_single_trial_dict(experiment.titer_dict)
    return data, t0


def parse_raw_data(format=None, id_type='CSV', file_name=None, data=None, experiment=None):
    if experiment is None:
        from .core.Experiment import Experiment
        experiment = Experiment()

    t0 = time.time()
    if format is None:
        raise Exception('No format defined')

    if data is None:
        if file_name is None:
            raise Exception('No data or file name given to load data from')

        # Get data from xlsx file
        print('\nImporting data from %s...' % (file_name),end='')
        # data = get_data(file_name)
        data = load_workbook(filename=file_name, data_only=True)
        print('%0.1fs' % (time.time()-t0))

    # Import parsers
    parser_case_dict = {'spectromax_OD' : spectromax_OD,
                        'tecan_OD'      : tecan_OD,
                        'default_titers': HPLC_titer_parser,
                        'spectromax_OD_triplicate': spectromax_OD_triplicate
                        }
    if format in parser_case_dict.keys():
        parser_case_dict[format](experiment, data=data, id_type=id_type)
    else:
        raise Exception('Parser %s not found', format)

    return experiment
