from .TimePoint import TimePoint
from .TrialIdentifier import TrialIdentifier
from collections import OrderedDict

def spectromax_OD(experiment, data):
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
                        temp_timepoint = TimePoint(temp_trial_identifier, 'OD600', time, data)

                        timepoint_list.append(temp_timepoint)
                    else:
                        print('Skipped time point')
        else:
            break

    experiment.parseTimePointCollection(timepoint_list)
