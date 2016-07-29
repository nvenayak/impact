
import ast  # Used to convert string literals to variables safely
import sys
import os

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect

from .forms import newExperimentForm, plot_options_form

from django.contrib.auth.views import *
# from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required

from sqlite3 import OperationalError

# Add the toolbox path
sys.path.append(os.path.join(os.path.dirname(__file__),'../../'))
import FermAT

# Set the default dbName, stored in the root directory
dbName = os.path.join(os.path.dirname(__file__),"../../default_FermAT_db.sqlite3")
default_input_format = 'default_OD'

# No login required
def welcome(request):
    return render(request,'FermAT_web/welcome.html')

def index(request):
    return render(request,'FermAT_web/login.html')

# Input views
@login_required
def new_experiment(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = newExperimentForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            expt = FermAT.Experiment(info=form.cleaned_data)
            expt_id = expt.db_commit(dbName)
            # redirect to a new URL:

            # Select a default input format and return the input data view
            return select_input_format(request, default_input_format, experiment_id = expt_id)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = newExperimentForm()

    request.session['selected_input_window'] = 'new_experiment'

    return render(request, 'FermAT_web/new_experiment.html', {'newExperimentForm': form,
                                                             'selected_input_window': request.session['selected_input_window']})

@login_required
def input(request):
    return select_input_format(request, default_input_format)

@login_required
def experimentSelect_input(request, experimentID):
    experimentID = int(experimentID)
    request.session['experiment_id'] = experimentID
    return select_input_format(request, request.session['input_format'], experiment_id = experimentID)

@login_required
def select_input_format(request, input_format, experiment_id = None):
    request.session['input_format'] = input_format
    request.session['selected_input_window'] = 'bulk_input'
    # request.session['experiment_id'] = int(experiment_id)
    if experiment_id is None:
        try:
            experiment_id = request.session['experiment_id']
        except KeyError:    pass

    if input_format == 'default_OD':
        column_labels = ['StrainID (CSV)'] + ['timepoint_'+str(n) for n in range(1,1000)]
        row_labels = ['Time (hours)'] + ['strain_'+str(n) for n in range(1,1000)]
    elif input_format == 'default_titers':
        row_labels = ['Titer name (BiGG)','Titer Type'] + ['titer_'+str(n) for n in range(1,20)]
        column_labels = ['Strain ID (CSV)'] + ['strain_'+str(n) for n in range(1,1000)]
    else:
        return HttpResponse('Invalid input_format')

    return render(request, 'FermAT_web/input.html', {'row_labels'     : row_labels,
                                                     'column_labels'  : column_labels,
                                                     'selected_layout': input_format,
                                                     'selected_input_window':request.session['selected_input_window'],
                                                     'mainWindow': 'input',
                                                     'experiment_id':experiment_id,
                                                     'exptInfo': FermAT.Project().getAllExperimentInfo_django(dbName)})


@login_required
def process_input_data(request):
    if request.method == 'POST':
        # print(request.POST)
        import json
        data = json.loads(request.body.decode('utf-8'))['data']

        print('Before processing:')
        print('Rows: ',len(data),'Columns: ',len(data[0]),'\n')

        # Remove empty rows
        emptyRows = 0
        emptyRowFound = False
        firstEmptyRowIndex = len(data)
        for i, row in enumerate(data):
            if row.count(None) == len(row) or row.count('') == len(row):
                emptyRows += 1
                if emptyRows == 1:
                    firstEmptyRowIndex = i
                    emptyRowFound = True
        if emptyRowFound:
            print('Empty rows: ',emptyRows)
            truncRowData = data[0:firstEmptyRowIndex]
        else: truncRowData = data

        # Remove empty columns
        truncData = []
        for i, truncRow in enumerate(truncRowData):
            firstEmptyElem = len(truncRow)
            for j, elem in enumerate(row):
                if elem == '':
                    firstEmptyElem = j
                    # emptyElemFound = True
            # truncRow = [elem for elem in row if elem != None and elem != '']
            truncData.append(truncRow[0:firstEmptyElem])
            if i == 0:
                rowLen = len(truncRow)
            if len(truncRow) != rowLen:
                print('Input array is jagged')

        print('After processing:')
        print('Rows: ',len(truncData),'Columns: ',len(truncData[0]))

        # Check if no data was entered
        if truncData[0][0] == '' and len(truncData)==1:
            noDataFound = True
            print('No data found: ',truncData)
        else:
            # Convert and check the types
            # cleanedData = []
            # print(truncData)
            converted_data = []
            for trunc_row in truncData:
                temp_row = []
                for elem in trunc_row:
                    try:
                        temp_elem = ast.literal_eval(elem)
                    except (ValueError, SyntaxError):
                        # Could not parse the literal, probably a string or empty, will use native format
                        temp_elem = elem
                    temp_row.append(temp_elem)
                converted_data.append(temp_row)

            # Load the data into the model
            expt = FermAT.Experiment()
            expt.db_load(dbName, experimentID = request.session['experiment_id'])

            if request.session['input_format'] == 'default_OD':
                input_format = 'NV_OD'
            elif request.session['input_format'] == 'default_titers':
                input_format = 'default_titers'
            else:
                raise Exception('Unknown data format selected')

            expt.parseRawData(input_format, data = converted_data) # Convert strings to floats
            experimentID = expt.db_commit(dbName)
            request.session['experiment_id'] = int(experimentID)

            update_experiments_from_db(request)

            return HttpResponse(json.dumps({'redirect': '/experimentSelect_analyze/'+str(experimentID)}), content_type="application/json")
    else:
        print('EXPECTED POST')

# Analyze Views
@login_required
def analyze(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = newExperimentForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = newExperimentForm()

    data = modifyMainPageSessionData(request, mainWindow = 'analyze')
    data['newExperimentForm'] = form

    return render(request, 'FermAT_web/analyze.html', data)

# Plot views
@login_required
def experimentSelect_analyze(request, experimentID):
    strainInfo = FermAT.Experiment().get_strains_django(dbName, experimentID)
    selectedExpt = FermAT.Experiment()
    selectedExpt.db_load(dbName,experimentID)
    exptInfo = selectedExpt.info
    request.session['strainInfo'] = strainInfo

    # Determine the unique identifiers for use in the sorting dropdown
    uniqueIDs = dict()
    for key in ['strainID','identifier1','identifier2']:
        uniqueIDs[key] = sorted(set([strain[key] for strain in strainInfo]))

    data = modifyMainPageSessionData(request, uniqueIDs = uniqueIDs)

    form = newExperimentForm(initial=exptInfo)
    # for field in form:
    #     print(field)
    # for field in exptInfo:
    #     getattr(form,field).initial = exptInfo[field]

    data['newExperimentForm'] = form
    data['experiment_id'] = int(experimentID)
    # selectedExpt.summary()
    return render(request, 'FermAT_web/analyze.html', data)

@login_required
def plot_options(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = plot_options_form(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            request.session['plot_options'] = form.cleaned_data

            request.session['prepared_plot_options'] = request.session['plot_options']
            if request.session['prepared_plot_options'] == []:
                request.session['prepared_plot_options'] = dict()
            else:
                request.session['prepared_plot_options']['cl_scales'] = ast.literal_eval(request.session['plot_options']['cl_scales'])
                if not request.session['prepared_plot_options']['use_stage_indices']:
                    request.session['prepared_plot_options']['stage_indices'] = None
                    request.session['prepared_plot_options']['stage'] = None
                else:
                    request.session['prepared_plot_options']['stage_indices'] = ast.literal_eval(request.session['plot_options']['stage_indices'])
                    request.session['prepared_plot_options']['stage'] = request.session['plot_options']['stage']

                del request.session['prepared_plot_options']['use_stage_indices']

                if request.session['plot_options']['sortBy'] == 'None':
                    print('in here5')
                    request.session['prepared_plot_options']['sortBy'] = None
            print(request.session['prepared_plot_options'])

            # redirect to a new URL:
            # data = modifyMainPageSessionData(request, mainWindow = 'plot')
            request.session['mainWindow'] = 'plot'
            data = updateFigure(request)
            # data = modifyMainPageSessionData(request)
            return render(request,'FermAT_web/home.html',data)

    # if a GET (or any other method) we'll create a blank form
    else:
        if request.session['plot_options'] != []:
            form = plot_options_form(initial=request.session['plot_options'])
        else:
            form = plot_options_form()

        data = modifyMainPageSessionData(request, mainWindow = 'plot_options')
        data['plot_options_form'] = form
        return render(request, 'FermAT_web/plot_options.html', data)

@login_required
def createAccount(request):
    from django.contrib.auth.models import User

    user = User.objects.create_user(request.POST['username'], request.POST['email'], request.POST['password'])
    pass

@login_required
def register(request):
    return HttpResponse('No registration page created')

@login_required()
def update_experiments_from_db(request):
    # Extract the info from the db, or create the db if an error is thrown
    try:
        exptInfo = FermAT.Project().getAllExperimentInfo_django(dbName)
    except OperationalError:
        FermAT.init_db(dbName)
        exptInfo = FermAT.Project().getAllExperimentInfo_django(dbName)

    data = modifyMainPageSessionData(request, exptInfo = exptInfo)

    return render(request, 'FermAT_web/home.html', data)

# @login_required
@login_required
def experimentSelect(request, experimentID):
    strainInfo = FermAT.Experiment().get_strains_django(dbName, experimentID)
    request.session['strainInfo'] = strainInfo
    request.session['experiment_id'] = int(experimentID)

    # Determine the unique identifiers for use in the sorting dropdown
    uniqueIDs = dict()
    for key in ['strainID','identifier1','identifier2']:
        uniqueIDs[key] = sorted(set([strain[key] for strain in strainInfo]))

    data = modifyMainPageSessionData(request, uniqueIDs = uniqueIDs)
    data['experiment_id'] = int(experimentID)
    return render(request, 'FermAT_web/home.html', data)


@login_required
def selectStrains(request):
    if request.method == 'POST':
        if 'strainsToPlot' in request.session.keys():
            strainsToPlot = request.session['strainsToPlot']
        else:
            strainsToPlot = []

        for strain in request.session['strainInfo']:
            if str(strain['replicateID']) in request.POST.keys():
                strainsToPlot.append(strain['replicateID'])

        if 'selectedStrainsInfo' not in request.session.keys():
            request.session['selectedStrainsInfo'] =  []

        request.session['selectedStrainsInfo'] =  request.session['selectedStrainsInfo'] + \
                                                  [strain for strain in request.session['strainInfo']
                                                   if ( strain['replicateID'] in strainsToPlot and
                                                        strain['replicateID'] not in [selectedStrain['replicateID'] for selectedStrain in request.session['selectedStrainsInfo']])]

        data = modifyMainPageSessionData(request, strainsToPlot = strainsToPlot,
                                         selectedStrainsInfo = request.session['selectedStrainsInfo'])
        updateFigure(request)
        # Determine the set of titers available for all selected strains
        data = modifyMainPageSessionData(request, titerNames = FermAT.Project().getTitersSelectedStrains_django(dbName, data['selectedStrainsInfo']))
    else:
        return HttpResponse('Expected POST for selectStrains')
    return render(request, 'FermAT_web/home.html',data)

@login_required
def removeStrains(request):
    if request.method == 'POST':
        request.session['selectedStrainsInfo'] = [strain for strain in request.session['selectedStrainsInfo'] if str(strain['replicateID']) not in request.POST.keys()]

        data = updateFigure(request)
        return render(request, 'FermAT_web/home.html',data)
    else:
        return HttpResponse('Expected POST data for /selectTiters/')

@login_required
def clearData(request):
    data = modifyMainPageSessionData(request, selectedStrainsInfo = [])

    return render(request, 'FermAT_web/home.html', data)

@login_required
def selectTiters(request):
    if request.method == 'POST':
        modifyMainPageSessionData(request, selectedTiters = [titer for titer in request.session['titerNames'] if titer in request.POST.keys()])
        data = updateFigure(request)
        return render(request, 'FermAT_web/home.html', data)
    else:
        return HttpResponse('Expected POST data for /selectTiters/')

@login_required
def selectStrainSubset(request):
    if request.method == 'POST':
        print(request.POST.keys())
        for key in request.POST.keys():
            print(request.POST[key])

        modifyMainPageSessionData(request)

        for strain in request.session['strainInfo']:
            if (strain['strainID'] == request.POST['strainID'] or request.POST['strainID'] == 'All')\
                    and (strain['identifier1'] == request.POST['identifier1'] or request.POST['identifier1'] == 'All') \
                    and (strain['identifier2'] == request.POST['identifier2'] or request.POST['identifier2'] == 'All') \
                    and strain['replicateID'] not in [selectedStrain['replicateID'] for selectedStrain in request.session['selectedStrainsInfo']]:
                request.session['selectedStrainsInfo'].append(strain)
        modifyMainPageSessionData(request, titerNames = FermAT.Project().getTitersSelectedStrains_django(dbName, request.session['selectedStrainsInfo']))
        data = updateFigure(request)
        return render(request, 'FermAT_web/home.html',data)
    else:
        return HttpResponse('Expected POST')

@login_required
def selectMainWindow(request, mainWindowSelection):
    update_experiments_from_db(request)
    if mainWindowSelection == 'plot':
        request.session['mainWindow'] = mainWindowSelection
        experiment = FermAT.Experiment()
        experiment.db_load(dbName, 1)
        updateFigure(request)
        data = modifyMainPageSessionData(request)
    elif mainWindowSelection == 'rawData':
        request.session['mainWindow'] = mainWindowSelection
        data = modifyMainPageSessionData(request)
    else:
        data = modifyMainPageSessionData(request)
    return render(request, 'FermAT_web/home.html',data)

def updateFigure(request):

    if 'mainWindow' in request.session.keys():
        if request.session['mainWindow'] == 'plot' and\
                len(request.session['selectedStrainsInfo']) > 0 and\
                len(request.session['selectedTiters']) > 0:
            print('in here')


            data = modifyMainPageSessionData(request, plotlyCode = FermAT.printGenericTimeCourse_plotly(dbName = dbName,
                                                                                                            strainsToPlot = [strain['replicateID'] for strain in request.session['selectedStrainsInfo']],
                                                                                                            titersToPlot = request.session['selectedTiters'],
                                                                                                            **request.session['prepared_plot_options']
                                                                                                            ))
        else:
             data = modifyMainPageSessionData(request)
    else:
         data = modifyMainPageSessionData(request)
    return data

@login_required
def modifyMainPageSessionData(request, **kwargs):
    data = dict()
    for key in ['strainInfo','exptInfo','selectedStrainsInfo','mainWindow', 'plotlyCode',
                'titerNames','strainsToPlot','uniqueIDs','selectedTiters','plot_options','prepared_plot_options']:
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

# Export functions
@login_required
def export_data(request):
    return render(request, 'FermAT_web/export.html', {'data':[1,2,3,4]})

@login_required
def experimentSelect_export(request, experimentID):
    expt = FermAT.Experiment()
    expt.db_load(dbName, int(experimentID))
    raw_data = expt.data()
    max_columns = max([len(row) for row in raw_data])
    squared_data = []
    for row in raw_data:
        row_len = len(row)
        temp_row = []
        for index in range(row_len):
            temp_row.append(row[index])
        for _ in range(row_len,max_columns):
            temp_row.append('')
        squared_data.append(temp_row)
    data = modifyMainPageSessionData(request)
    data['data_body'] = squared_data
    print(raw_data)
    print(squared_data)
    return render(request, 'FermAT_web/export.html', data)


@login_required
def export(request):

    return render(request, 'FermAT_web/export.html', modifyMainPageSessionData(request, mainWindow = 'export'))

@login_required
def iPython(request):
    return render(request, 'FermAT_web/iPython.html')