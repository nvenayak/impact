

def spectromax_OD(experiment, data):
    from .Experiment import Experiment
    from .TimePoint import TimePoint
    from .TrialIdentifier import TrialIdentifier

    from collections import OrderedDict

    # This should be an ordered dict if imported from py_xlsx
    assert isinstance(data, OrderedDict)

    assert isinstance(experiment, Experiment)

    identifiers = data['identifiers']
    data = data['OD']

    # The data starts at (3,2) and is in a 8x12 format
    timepoint_list = []
    for start_row_index in range(3, len(data['OD'][0]), 13):
        # Parse the time point out first
        parsed_time = data[start_row_index][0].split(':')
        if len(parsed_time > 2):
            time = parsed_time[0] * 3600 + parsed_time[1] * 60 + parsed_time[2]
        else:
            time = parsed_time[0] * 60 + parsed_time[1]

        time = time / 3600  # convert to hours

        plate_data = data[start_row_index:start_row_index + 8][start_row_index:start_row_index + 12]

        for row, i in enumerate(plate_data):
            for data, j in enumerate(row):
                temp_trial_identifier = TrialIdentifier()
                temp_trial_identifier.parse_trial_identifier_from_csv(data['identifier'][i][j])
                temp_timepoint = TimePoint(temp_trial_identifier, 'OD600', time, data)

                timepoint_list.append(temp_timepoint)

    experiment.parseTimePointCollection(timepoint_list)
