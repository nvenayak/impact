# coding=utf-8
"""
Logic for input.html
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse

from .tools import update_experiments_from_db
from ..forms import newExperimentForm, analysis_options_form, UploadFileForm

import impact
from impact.core.settings import settings
db_name = settings.db_name

from io import StringIO

import sys
import ast

default_input_format = 'default_titers'

@login_required
def new_experiment(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = newExperimentForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            expt = impact.Experiment(info=form.cleaned_data)
            expt_id = expt.db_commit(db_name)
            request.session['experiment_id'] = expt_id

            # Select a default input format and return the input data view
            return select_input_format(request, default_input_format, experiment_id=expt_id)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = newExperimentForm()

    request.session['selected_input_window'] = 'new_experiment'

    return render(request, 'impact_cloud/new_experiment.html',
                  {'newExperimentForm': form,
                   'selected_input_window': request.session['selected_input_window']})


@login_required
def input(request):
    return select_input_format(request, default_input_format)

@login_required
def input_file(request):
    return render(request, 'impact_cloud/input_file.html', {'upload_file_form':UploadFileForm()})

@login_required
def analysis_options(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = analysis_options_form(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            expt = impact.Experiment(info=form.cleaned_data)
            expt_id = expt.db_commit(db_name)
            request.session['experiment_id'] = expt_id
            # redirect to a new URL:

            # Select a default input format and return the input data view
            return select_input_format(request, default_input_format, experiment_id=expt_id)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = analysis_options_form()

    request.session['selected_input_window'] = 'analysis_options'

    return render(request, 'impact_cloud/analysis_options.html',
                  {'analysis_options_form': form,
                   'selected_input_window': request.session['selected_input_window']})

@login_required
def experiment_select_input(request, experiment_id):
    experiment_id = int(experiment_id)
    request.session['experiment_id'] = experiment_id
    return select_input_format(request, request.session['input_format'], experiment_id = experiment_id)


@login_required
def input_initial(request):
    return render(request, 'impact_cloud/input.html', {'selected_input_window':'home',
                                                     'mainWindow': 'input'})

@login_required
def select_input_format(request, input_format, experiment_id=None):
    request.session['input_format'] = input_format
    request.session['selected_input_window'] = 'table_input'
    # request.session['experiment_id'] = int(experiment_id)
    if experiment_id is None:
        # load the experiment if there is one
        try:
            experiment_id = request.session['experiment_id']
        except KeyError:
            pass

    update_experiments_from_db(request)

    if input_format == 'default_OD':
        column_labels = ['StrainID (CSV)'] + ['timepoint_'+str(n) for n in range(1,1000)]
        row_labels = ['Time (hours)'] + ['strain_'+str(n) for n in range(1,1000)]
    elif input_format == 'default_titers':
        row_labels = ['Analyte name (BiGG)','Analyte type'] + ['timepoint_'+str(n) for n in range(1,20)]
        column_labels = ['Strain ID (CSV)'] + ['Analyte_'+str(n) for n in range(1,1000)]
    else:
        return HttpResponse('Invalid input_format')

    return render(request, 'impact_cloud/table_input.html', {'row_labels': row_labels,
                                                     'column_labels': column_labels,
                                                     'selected_layout': input_format,
                                                     'selected_input_window': request.session['selected_input_window'],
                                                     'mainWindow': 'input',
                                                     'experiment_id': experiment_id,
                                                     'exptInfo': request.session['exptInfo']})

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
            expt = impact.Experiment()
            new_expt = impact.Experiment()
            expt.db_load(db_name, experiment_id = request.session['experiment_id'])

            if request.session['input_format'] == 'default_OD':
                input_format = 'NV_OD'
            elif request.session['input_format'] == 'default_titers':
                input_format = 'default_titers'
            else:
                raise Exception('Unknown data format selected')



            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()

            try:
                # Parse the new data and combine the experiments. The info from the original experiment will be maintained
                new_expt.parse_raw_data(input_format, data = converted_data) # Convert strings to floats
                expt = expt + new_expt

                experiment_id = expt.db_commit(db_name, overwrite_experiment_id=request.session['experiment_id'])
                request.session['experiment_id'] = int(experiment_id)
                processing_std_out = mystdout.getvalue()
                console_output = '<h3> Analysis complete:</h3>'+'<pre>'+processing_std_out+'</pre>'
                redirect_url = '/experimentSelect_analyze/'+str(experiment_id)
            except Exception as e:
                import traceback
                traceback.print_exc(file=mystdout)
                # print(e)
                processing_std_out = mystdout.getvalue()
                print(processing_std_out)
                console_output = '<h3> Processing error:</h3>'+'<pre>'+processing_std_out+'</pre>'
                redirect_url = '#'

            sys.stdout = old_stdout
            update_experiments_from_db(request)
            # return experimentSelect_analyze(request, experiment_id)
            return HttpResponse(json.dumps({'redirect': redirect_url,
                                            'console_output':console_output}),
                                content_type="application/json")
    else:
        print('EXPECTED POST')