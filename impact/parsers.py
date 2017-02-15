from .core.AnalyteData import TimePoint
from .core.TrialIdentifier import TrialIdentifier, Strain
from collections import OrderedDict
import time as sys_time
import numpy as np
import copy
import datetime

# "strain_ko=adh,pta;strain_gen1=D1;plasmid_name=pKDL071;inducer=IPTG"
#
# 'var_val_delim ='
# 'id_delim ;'


def generic_id_parser(self, id, id_val_delim='=', id_delim=';'):
    assert isinstance(id,str)

    pairs = id.split(id_delim)
    id_val = {pair.split(id_val_delim)[0] : pair.split(id_val_delim)[1] for pair in pairs}

    strain = Strain()
    if 'strain_ko' in id_val.keys():
        strain.knockouts = id_val['strain_ko']



    return id_val

def spectromax_OD(experiment, data, fileName = None):
    from .core.settings import settings
    live_calculations = settings.live_calculations
    
    # This should be an ordered dict if imported from py_xlsx
    assert isinstance(data, OrderedDict)


    identifiers = data['identifiers']
    raw_data = data['data']

    # The data starts at (3,2) and is in a 8x12 format
    timepoint_list = []

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

            time = time / 3600  # convert to hours

            # Define the data for a single plate, single timepoint
            plate_data = [row[2:14] for row in raw_data[start_row_index:start_row_index+8]]
            # print(plate_data)

            # Load the data point by point
            for i, row in enumerate(plate_data):
                for j, data in enumerate(row):
                    # Skip wells where no identifier is listed
                    if identifiers[i][j] != '':
                        temp_trial_identifier = TrialIdentifier()
                        temp_trial_identifier.parse_trial_identifier_from_csv(identifiers[i][j])
                        temp_trial_identifier.analyte_type = 'biomass'
                        temp_trial_identifier.analyte_name = 'OD600'
                        temp_timepoint = TimePoint(temp_trial_identifier, 'OD600', time, float(data))

                        timepoint_list.append(temp_timepoint)
                    else:
                        print('Skipped time point')
        else:
            break

    experiment.parse_time_point_dict(timepoint_list)

    if live_calculations:   experiment.calculate()

def HPLC_titer_parser(experiment, data, fileName):
    t0 = sys_time.time()

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
    timepoint_list = []
    for i in range(first_data_row, len(data['titers'])):
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
                timepoint_list.append(
                    TimePoint(copy.copy(temp_run_identifier_object),
                              temp_run_identifier_object.time,
                              data['titers'][i][analyte_nameColumn[key]]))

        else:
            skipped_lines += 1
    tf = sys_time.time()
    print("Parsed %i timeCourseObjects in %0.3fs\n" % (len(timepoint_list), tf - t0))
    print("Number of lines skipped: ", skipped_lines)
    experiment.parse_time_point_dict(timepoint_list)
    experiment.calculate()

def tecan_OD(experiment, data, fileName, t0):
    from .AnalyteData import TimeCourse

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
        temp_run_identifier_object = TrialIdentifier()
        if type(row[0]) is str:
            temp_run_identifier_object.parse_trial_identifier_from_csv(row[0])
            temp_run_identifier_object.analyte_name = 'OD600'
            temp_run_identifier_object.analyte_type = 'biomass'
            temp_time_course = TimeCourse()
            temp_time_course.trial_identifier = temp_run_identifier_object

            # Data in seconds, data required to be in hours
            temp_time_course.time_vector = np.array(np.divide(data[0][1:], 3600))

            temp_time_course.data_vector = np.array(row[1:])
            experiment.titer_dict[temp_time_course.getTimeCourseID()] = copy.copy(temp_time_course)
    tf = sys_time.time()
    print("Parsed %i timeCourseObjects in %0.3fs\n" % (len(experiment.titer_dict), tf - t0))
    experiment.parse_analyte_data_dict(experiment.titer_dict)
    return data, t0