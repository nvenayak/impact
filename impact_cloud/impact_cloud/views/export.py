from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .tools import modifyMainPageSessionData

import numpy as np

from impact.core.settings import settings
db_name = settings.db_name
import impact

@login_required
def export_data(request):
    return render(request, 'impact_cloud/export.html', {'data':[1,2,3,4]})


@login_required
def experimentSelect_export(request, experiment_id):
    expt = impact.Experiment()
    expt.db_load(db_name, int(experiment_id))
    print('loaded experiment')
    raw_data = expt.data()
    max_columns = max([len(row) for row in raw_data])
    squared_data = []
    for row in raw_data:
        row_len = len(row)
        temp_row = []
        for index in range(row_len):
            flag = True
            # Check if a number is not nan
            if type(row[index]) is not str:
                if np.isnan(row[index]):
                    flag = False
                    temp_row.append('nan')
            if flag:
                temp_row.append(row[index])
        for _ in range(row_len,max_columns):
            temp_row.append('')
        squared_data.append(temp_row)
    print('finished getting the data')
    data = modifyMainPageSessionData(request)
    data['data_body'] = squared_data

    return render(request, 'impact_cloud/export.html', data)


@login_required
def export(request):
    return render(request, 'impact_cloud/export.html', modifyMainPageSessionData(request, mainWindow = 'export'))