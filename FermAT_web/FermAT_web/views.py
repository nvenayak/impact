import ast  # Used to convert string literals to variables safely
import sys
import os

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages

from .forms import *

from django.contrib.auth.views import *
# from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.signals import user_logged_in

from sqlite3 import OperationalError

# Add the toolbox path
sys.path.append(os.path.join(os.path.dirname(__file__),'../../'))
import FermAT
import FermAT.settings

from io import StringIO
import sys
import copy

# Set the default db_name, stored in the root directory
db_name = FermAT.settings.db_name   # os.path.join(os.path.dirname(__file__),"../../default_FermAT_db.sqlite3")
default_input_format = 'default_titers'

FermAT.init_db(db_name=db_name)

def logged_in_message(sender, user, request, **kwargs):
    """
    Add a welcome message when the user logs in
    """
    messages.info(request, "Successfully logged in as: "+request.user.username+". Welcome..")

user_logged_in.connect(logged_in_message)

# No login required
def welcome(request):
    return render(request,'FermAT_web/welcome.html')


def index(request):
    return render(request,'FermAT_web/login.html')

def color_scale_examples(request):
    import colorlover as cl
    ordered_numbers = ['3','4','5','6','7','8','9','10','11','12']
    output = ''
    for number in ordered_numbers:
        output += '<h3>'+number+' colors</h3>'
        for type in cl.scales[number]:
            output += '<h4>'+type+'</h4>'
            output += cl.to_html(cl.scales[number][type])
            # for scale in cl.scales[number][type]:
            #     output += 'Scale: '+scale
            #     output += cl.to_html(cl.scales[number][type][scale])
            # output += '<br>'

    from collections import OrderedDict


    # ordered_numbers.sort()
    # print(ordered_numbers)
    ordered_scales = OrderedDict([(ordered_number,cl.scales[ordered_number]) for ordered_number in ordered_numbers])


    return HttpResponse(output)

@login_required
def download_plot(request):
    file_name = FermAT.printGenericTimeCourse_plotly(dbName=db_name,
                                         strainsToPlot=[strain['replicateID'] for strain in
                                                        request.session['selectedStrainsInfo']],
                                         titersToPlot=request.session['selectedTiters'],
                                         output_type='image', format='poster',img_scale=10,
                                         **request.session['prepared_plot_options']
                                         )
    image_data = open(file_name,'rb').read()
    return HttpResponse(image_data, content_type="image/png")

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
            expt_id = expt.db_commit(db_name)
            request.session['experiment_id'] = expt_id
            # redirect to a new URL:

            # Select a default input format and return the input data view
            return select_input_format(request, default_input_format, experiment_id=expt_id)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = newExperimentForm()

    request.session['selected_input_window'] = 'new_experiment'

    return render(request, 'FermAT_web/new_experiment.html',
                  {'newExperimentForm': form,
                   'selected_input_window': request.session['selected_input_window']})


@login_required
def input(request):
    return select_input_format(request, default_input_format)

@login_required
def analysis_options(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = analysis_options_form(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            expt = FermAT.Experiment(info=form.cleaned_data)
            expt_id = expt.db_commit(db_name)
            request.session['experiment_id'] = expt_id
            # redirect to a new URL:

            # Select a default input format and return the input data view
            return select_input_format(request, default_input_format, experiment_id=expt_id)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = analysis_options_form()

    request.session['selected_input_window'] = 'analysis_options'

    return render(request, 'FermAT_web/analysis_options.html',
                  {'analysis_options_form': form,
                   'selected_input_window': request.session['selected_input_window']})

@login_required
def experiment_select_input(request, experiment_id):
    experiment_id = int(experiment_id)
    request.session['experiment_id'] = experiment_id
    return select_input_format(request, request.session['input_format'], experiment_id = experiment_id)


@login_required
def input_initial(request):
    return render(request, 'FermAT_web/input.html', {'selected_input_window':'home',
                                                     'mainWindow': 'input'})

@login_required
def select_input_format(request, input_format, experiment_id=None):
    request.session['input_format'] = input_format
    request.session['selected_input_window'] = 'table_input'
    # request.session['experiment_id'] = int(experiment_id)
    if experiment_id is None:
        try:
            experiment_id = request.session['experiment_id']
        except KeyError:    pass

    if input_format == 'default_OD':
        column_labels = ['StrainID (CSV)'] + ['timepoint_'+str(n) for n in range(1,1000)]
        row_labels = ['Time (hours)'] + ['strain_'+str(n) for n in range(1,1000)]
    elif input_format == 'default_titers':
        row_labels = ['Analyte name (BiGG)','Analyte type'] + ['timepoint_'+str(n) for n in range(1,20)]
        column_labels = ['Strain ID (CSV)'] + ['Analyte_'+str(n) for n in range(1,1000)]
    else:
        return HttpResponse('Invalid input_format')

    return render(request, 'FermAT_web/table_input.html', {'row_labels': row_labels,
                                                     'column_labels': column_labels,
                                                     'selected_layout': input_format,
                                                     'selected_input_window': request.session['selected_input_window'],
                                                     'mainWindow': 'input',
                                                     'experiment_id': experiment_id,
                                                     'exptInfo': FermAT.Project().getAllExperimentInfo_django(db_name)})


@login_required
def process_input_data(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body.decode('utf-8'))['data']

        print('Before processing:')
        print('Rows: ',len(data),'Columns: ',len(data[0]),'\n')

        # Remove empty rows
        empty_rows = 0
        empty_row_found = False
        first_empty_row_index = len(data)
        for i, row in enumerate(data):
            if row.count(None) == len(row) or row.count('') == len(row):
                empty_rows += 1
                if empty_rows == 1:
                    first_empty_row_index = i
                    empty_row_found = True
        if empty_row_found:
            print('Empty rows: ',empty_rows)
            truncated_row_data = data[0:first_empty_row_index]
        else: truncated_row_data = data

        # Remove empty columns
        truncData = []
        for i, truncRow in enumerate(truncated_row_data):
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
            expt.db_load(db_name, experiment_id = request.session['experiment_id'])

            if request.session['input_format'] == 'default_OD':
                input_format = 'NV_OD'
            elif request.session['input_format'] == 'default_titers':
                input_format = 'default_titers'
            else:
                raise Exception('Unknown data format selected')



            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()

            expt.parseRawData(input_format, data = converted_data) # Convert strings to floats

            sys.stdout = old_stdout
            import html
            processing_std_out = mystdout.getvalue()
            # print(processing_std_out)
            processing_std_out = html.escape(processing_std_out)
            # print(processing_std_out)

            experiment_id = expt.db_commit(db_name, overwrite_experiment_id=request.session['experiment_id'])
            request.session['experiment_id'] = int(experiment_id)

            update_experiments_from_db(request)
            # return experimentSelect_analyze(request, experiment_id)
            return HttpResponse(json.dumps({'redirect': '/experimentSelect_analyze/'+str(experiment_id),
                                            'console_output':processing_std_out}), content_type="application/json")
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
            expt = FermAT.Experiment()
            expt.db_load(db_name = db_name, experiment_id=request.session['experiment_id'])
            expt.info = form.cleaned_data
            experiment_id = expt.db_commit(db_name, overwrite_experiment_id=request.session['experiment_id'])
            return experimentSelect_analyze(request, experiment_id)
    # if a GET (or any other method) we'll create a blank form
    else:
        form = newExperimentForm()

        data = modifyMainPageSessionData(request, mainWindow = 'analyze')
        data['newExperimentForm'] = form

        return render(request, 'FermAT_web/analyze.html', data)

@login_required
def delete_experiment(request, experiment_id):
    FermAT.Experiment().db_delete(db_name, experiment_id)
    update_experiments_from_db(request)
    return analyze(request)

# Plot views
@login_required
def experimentSelect_analyze(request, experiment_id):
    strainInfo = FermAT.Experiment().get_strains_django(db_name, experiment_id)
    selectedExpt = FermAT.Experiment()
    selectedExpt.db_load(db_name, experiment_id)
    exptInfo = selectedExpt.info
    request.session['strainInfo'] = strainInfo

    # Determine the unique identifiers for use in the sorting dropdown
    uniqueIDs = dict()
    for key in ['strain_id','id_1','id_2']:
        uniqueIDs[key] = sorted(set([strain[key] for strain in strainInfo]))

    data = modifyMainPageSessionData(request, uniqueIDs = uniqueIDs)

    form = newExperimentForm(initial=exptInfo)
    # for field in form:
    #     print(field)
    # for field in exptInfo:
    #     getattr(form,field).initial = exptInfo[field]

    data['newExperimentForm'] = form
    data['experiment_id'] = int(experiment_id)

    experiment = FermAT.Experiment()
    experiment.db_load(db_name=db_name, experiment_id = int(experiment_id))
    # print(vars(experiment))
    # print(experiment.titer_dict)
    replicate_info = []
    for key in experiment.replicate_experiment_dict:
        replicate = experiment.replicate_experiment_dict[key]
        temp = {}
        for attr in ['strain_id','id_1','id_2']:
            temp[attr] = getattr(replicate.trial_identifier,attr)

        # Get unique titers
        titers = []
        for single_trial in replicate.single_trial_list:
            [titers.append(analyte) for analyte in [single_trial.biomass_name] + [single_trial.substrate_name] + single_trial.product_names]
        unique_titers = list(set(titers))
        temp['number_of_analytes'] = len(unique_titers)
        temp['replicate_id'] = replicate.db_replicate_id

        temp['number_of_replicates'] = len(replicate.single_trial_list)
        replicate_info.append(temp)
    data['replicate_info'] = replicate_info
    data['analyze_tab'] = 'replicate'
    print(replicate_info)
    return render(request, 'FermAT_web/analyze.html', data)

@login_required
def analyze_select_replicate(request, replicate_id):
    replicate = FermAT.ReplicateTrial()
    replicate.db_load(db_name=db_name, replicateID = int(replicate_id))

    titers = []
    for single_trial in replicate.single_trial_list:
        titers = [analyte for analyte in
         [single_trial.biomass_name] + [single_trial.substrate_name] + single_trial.product_names]
    unique_titers = list(set(titers))
    data = modifyMainPageSessionData(request)
    data['analytes'] = unique_titers
    data['analyze_tab'] = 'analyte'
    form = newExperimentForm()
    data['newExperimentForm'] = form

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

            # Make a copy to ensure that the form default values remain correct
            request.session['prepared_plot_options'] = copy.copy(request.session['plot_options'])

            # Prepare yield_titer_select information
            if request.session['plot_options']['yield_titer_select'] == 'yieldFlag':
                request.session['prepared_plot_options']['yieldFlag'] = True
                request.session['prepared_plot_options']['titerFlag'] = False
            elif request.session['plot_options']['yield_titer_select'] == 'titerFlag':
                request.session['prepared_plot_options']['yieldFlag'] = False
                request.session['prepared_plot_options']['titerFlag'] = True
            else:
                raise Exception('Unexpected value')

            # Delete the entry from the prepared data, it is not required for plotting
            if 'yield_titer_select' in request.session['prepared_plot_options'].keys():
                del request.session['prepared_plot_options']['yield_titer_select']

            # Set the plot type
            if request.session['plot_options']['plot_type'] == 'endpoint':
                request.session['prepared_plot_options']['endpointFlag'] = True
            elif request.session['plot_options']['plot_type'] == 'timecourse':
                request.session['prepared_plot_options']['endpointFlag'] = False
            else:
                raise Exception('Unexpected value: '+request.session['plot_options']['plot_type'])

            # Remove plot_type as it is not a plotting parameter
            if 'plot_type' in request.session['prepared_plot_options'].keys():
                del request.session['prepared_plot_options']['plot_type']

            # Extract info from form regarding stages and clean up
            if request.session['prepared_plot_options'] == []:
                request.session['prepared_plot_options'] = dict()
            request.session['prepared_plot_options']['cl_scales'] = ast.literal_eval(request.session['plot_options']['cl_scales'])
            if not request.session['prepared_plot_options']['use_stage_indices']:
                request.session['prepared_plot_options']['stage_indices'] = None
                request.session['prepared_plot_options']['stage'] = None
            else:
                request.session['prepared_plot_options']['stage_indices'] = ast.literal_eval(request.session['plot_options']['stage_indices'])
                request.session['prepared_plot_options']['stage'] = request.session['plot_options']['stage']

            del request.session['prepared_plot_options']['use_stage_indices']

            # Extract sort by information
            if request.session['plot_options']['sortBy'] == 'None':
                print('in here5')
                request.session['prepared_plot_options']['sortBy'] = None

            request.session['mainWindow'] = 'plot'
            data = updateFigure(request)

            return render(request,'FermAT_web/plot.html',data)

    # if a GET (or any other method) we'll create a blank form
    else:
        if request.session['plot_options'] != []:
            print(request.session['plot_options'])
            print('using above session info')
            form = plot_options_form(initial=request.session['plot_options'])
        else:
            print('using empty form')
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
        exptInfo = FermAT.Project().getAllExperimentInfo_django(db_name)
    except OperationalError:
        FermAT.init_db(db_name)
        exptInfo = FermAT.Project().getAllExperimentInfo_django(db_name)

    data = modifyMainPageSessionData(request, exptInfo = exptInfo)

    # return render(request, 'FermAT_web/plot.html', data)

@login_required
def experimentSelect(request, experiment_id):
    strainInfo = FermAT.Experiment().get_strains_django(db_name, experiment_id)
    request.session['strainInfo'] = strainInfo
    request.session['experiment_id'] = int(experiment_id)

    # Determine the unique identifiers for use in the sorting dropdown
    uniqueIDs = dict()
    for key in ['strain_id','id_1','id_2']:
        uniqueIDs[key] = sorted(set([strain[key] for strain in strainInfo]))

    data = modifyMainPageSessionData(request, uniqueIDs = uniqueIDs, experiment_id = int(experiment_id))

    return render(request, 'FermAT_web/plot.html', data)


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
        data = modifyMainPageSessionData(request, analyte_names = FermAT.Project().getTitersSelectedStrains_django(db_name, data['selectedStrainsInfo']))
    else:
        return HttpResponse('Expected POST for selectStrains')
    return render(request, 'FermAT_web/plot.html',data)

@login_required
def removeStrains(request):
    if request.method == 'POST':
        request.session['selectedStrainsInfo'] = [strain for strain in request.session['selectedStrainsInfo'] if str(strain['replicateID']) not in request.POST.keys()]
        request.session['strainsToPlot'] = [strain['replicateID'] for strain in request.session['selectedStrainsInfo'] if str(strain['replicateID']) not in request.POST.keys()]
        data = updateFigure(request)
        return render(request, 'FermAT_web/plot.html',data)
    else:
        return HttpResponse('Expected POST data for plot/select_titers/')


@login_required
def clearData(request):
    data = modifyMainPageSessionData(request, selectedStrainsInfo = [], strainsToPlot=[])
    return render(request, 'FermAT_web/plot.html', data)

@login_required
def selectTiters(request):
    if request.method == 'POST':
        modifyMainPageSessionData(request, selectedTiters = [titer for titer in request.session['analyte_names'] if titer in request.POST.keys()])
        data = updateFigure(request)
        return render(request, 'FermAT_web/plot.html', data)
    else:
        return HttpResponse('Expected POST data for post/select_titers/')

@login_required
def selectStrainSubset(request):
    if request.method == 'POST':
        print(request.POST.keys())
        for key in request.POST.keys():
            print(request.POST[key])

        modifyMainPageSessionData(request)

        for strain in request.session['strainInfo']:
            if (strain['strain_id'] == request.POST['strain_id'] or request.POST['strain_id'] == 'All')\
                    and (strain['id_1'] == request.POST['id_1'] or request.POST['id_1'] == 'All') \
                    and (strain['id_2'] == request.POST['id_2'] or request.POST['id_2'] == 'All') \
                    and strain['replicateID'] not in [selectedStrain['replicateID'] for selectedStrain in request.session['selectedStrainsInfo']]:
                request.session['selectedStrainsInfo'].append(strain)
        modifyMainPageSessionData(request, analyte_names = FermAT.Project().getTitersSelectedStrains_django(db_name, request.session['selectedStrainsInfo']))
        data = updateFigure(request)
        return render(request, 'FermAT_web/plot.html',data)
    else:
        return HttpResponse('Expected POST')

@login_required
def selectMainWindow(request, mainWindowSelection):
    update_experiments_from_db(request)
    if mainWindowSelection == 'plot':
        request.session['mainWindow'] = mainWindowSelection
        experiment = FermAT.Experiment()
        experiment.db_load(db_name, 1)
        updateFigure(request)
        data = modifyMainPageSessionData(request)
    elif mainWindowSelection == 'rawData':
        request.session['mainWindow'] = mainWindowSelection
        data = modifyMainPageSessionData(request)
    else:
        data = modifyMainPageSessionData(request)
    return render(request, 'FermAT_web/plot.html',data)

@login_required
def plot(request):
    request.session['mainWindow'] = 'plot'
    # experiment = FermAT.Experiment()
    try:
        update_experiments_from_db(request)
    except IndexError as e:
        modifyMainPageSessionData(request, plotlyCode = '<h4> Please first import and select data to plot </h4>')
        pass
    else:
        updateFigure(request)
    data = modifyMainPageSessionData(request)

    return render(request, 'FermAT_web/plot.html', data)

@login_required
def updateFigure(request):

    if 'mainWindow' in request.session.keys():
        if request.session['mainWindow'] == 'plot' and\
                len(request.session['selectedStrainsInfo']) > 0 and\
                len(request.session['selectedTiters']) > 0:
            print('in here')


            data = modifyMainPageSessionData(request, plotlyCode = FermAT.printGenericTimeCourse_plotly(dbName = db_name,
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

# Export functions
@login_required
def export_data(request):
    return render(request, 'FermAT_web/export.html', {'data':[1,2,3,4]})

@login_required
def experimentSelect_export(request, experiment_id):
    expt = FermAT.Experiment()
    expt.db_load(db_name, int(experiment_id))
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
    # print(raw_data)
    # print(squared_data)
    return render(request, 'FermAT_web/export.html', data)


@login_required
def export(request):

    return render(request, 'FermAT_web/export.html', modifyMainPageSessionData(request, mainWindow = 'export'))

@login_required
def iPython(request):
    return render(request, 'FermAT_web/iPython.html')

@login_required
def iPython_auth(request):
    # https://developers.shopware.com/blog/2015/03/02/sso-with-nginx-authrequest-module/
    pass
    # if user is authenticated
        # spin up docker container
        # return autheticated
    # else
        # return unautheticated