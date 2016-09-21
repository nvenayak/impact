from django.contrib.auth.decorators import login_required
from sqlite3 import OperationalError

from FermAT.settings import db_name
import FermAT

@login_required
def modifyMainPageSessionData(request, **kwargs):
    data = dict()
    for key in ['strainInfo','exptInfo','selectedStrainsInfo','mainWindow', 'plotlyCode', 'experiment_id',
                'analyte_names','strainsToPlot','uniqueIDs','selectedTiters','plot_options','prepared_plot_options']:
        if key in kwargs:
            data[key] = kwargs[key]
            request.session[key] = kwargs[key]
        elif key in request.session.keys():
            data[key] = request.session[key]
        else:
            if key in ['plot_options','prepared_plot_options']:
                data[key] = dict()
                request.session[key] = dict()
            else:
                data[key] = []
                request.session[key] = []

    return data

@login_required()
def update_experiments_from_db(request):
    # Extract the info from the db, or create the db if an error is thrown
    try:
        exptInfo = FermAT.Project().getAllExperimentInfo_django(db_name)
    except OperationalError:
        FermAT.init_db(db_name)
        exptInfo = FermAT.Project().getAllExperimentInfo_django(db_name)

    modifyMainPageSessionData(request, exptInfo = exptInfo)