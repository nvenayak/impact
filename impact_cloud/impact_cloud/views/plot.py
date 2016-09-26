from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse

from .tools import modifyMainPageSessionData, update_experiments_from_db
from ..forms import plot_options_form

from impact.settings import db_name
import impact
import copy
import ast
from collections import OrderedDict

@login_required
def clear_data(request):
    data = modifyMainPageSessionData(request, selectedStrainsInfo = [], strainsToPlot=[])
    return render(request, 'impact_cloud/plot.html', data)

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

            return render(request,'impact_cloud/plot.html',data)

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
        return render(request, 'impact_cloud/plot_options.html', data)

@login_required
def updateFigure(request):

    if 'mainWindow' in request.session.keys():
        if request.session['mainWindow'] == 'plot' and\
                len(request.session['selectedStrainsInfo']) > 0 and\
                len(request.session['selectedTiters']) > 0:
            print('in here')


            data = modifyMainPageSessionData(request, plotlyCode = impact.printGenericTimeCourse_plotly(dbName = db_name,
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
def experimentSelect(request, experiment_id):
    strainInfo = impact.Experiment().get_strains_django(db_name, experiment_id)
    request.session['strainInfo'] = strainInfo
    request.session['experiment_id'] = int(experiment_id)

    # Determine the unique identifiers for use in the sorting dropdown
    uniqueIDs = dict()
    for key in ['strain_id','id_1','id_2']:
        uniqueIDs[key] = sorted(set([strain[key] for strain in strainInfo]))

    data = modifyMainPageSessionData(request, uniqueIDs = uniqueIDs, experiment_id = int(experiment_id))

    return render(request, 'impact_cloud/plot.html', data)


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
        data = modifyMainPageSessionData(request, analyte_names = impact.Project().getTitersSelectedStrains_django(db_name, data['selectedStrainsInfo']))
    else:
        return HttpResponse('Expected POST for selectStrains')
    return render(request, 'impact_cloud/plot.html',data)

@login_required
def removeStrains(request):
    if request.method == 'POST':
        request.session['selectedStrainsInfo'] = [strain for strain in request.session['selectedStrainsInfo'] if str(strain['replicateID']) not in request.POST.keys()]
        request.session['strainsToPlot'] = [strain['replicateID'] for strain in request.session['selectedStrainsInfo'] if str(strain['replicateID']) not in request.POST.keys()]
        data = updateFigure(request)
        return render(request, 'impact_cloud/plot.html',data)
    else:
        return HttpResponse('Expected POST data for plot/select_titers/')




@login_required
def selectTiters(request):
    if request.method == 'POST':
        modifyMainPageSessionData(request, selectedTiters = [titer for titer in request.session['analyte_names'] if titer in request.POST.keys()])
        data = updateFigure(request)
        return render(request, 'impact_cloud/plot.html', data)
    else:
        return HttpResponse('Expected POST data for post/select_titers/')

@login_required
def plot(request):
    request.session['mainWindow'] = 'plot'
    # experiment = impact.Experiment()
    try:
        update_experiments_from_db(request)
    except IndexError as e:
        modifyMainPageSessionData(request, plotlyCode = '<h4> Please first import and select data to plot </h4>')
        pass
    else:
        updateFigure(request)
    data = modifyMainPageSessionData(request)

    return render(request, 'impact_cloud/plot.html', data)

def color_scale_examples(request):
    """
    Return a HttpResponse with the colorlover color scales.
    """
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

    # ordered_numbers.sort()
    # print(ordered_numbers)
    ordered_scales = OrderedDict([(ordered_number,cl.scales[ordered_number]) for ordered_number in ordered_numbers])

    return HttpResponse(output)

@login_required
def select_strain_subset(request):
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
        modifyMainPageSessionData(request, analyte_names = impact.Project().getTitersSelectedStrains_django(db_name, request.session['selectedStrainsInfo']))
        data = updateFigure(request)
        return render(request, 'impact_cloud/plot.html',data)
    else:
        return HttpResponse('Expected POST')