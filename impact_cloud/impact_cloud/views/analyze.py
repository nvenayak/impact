from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .tools import modifyMainPageSessionData, update_experiments_from_db
from ..forms import newExperimentForm

from impact.settings import db_name
import impact


@login_required
def analyze_select_replicate(request, replicate_id):
    replicate = impact.ReplicateTrial()
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

    return render(request, 'impact_cloud/analyze.html', data)

@login_required
def analyze_select_analyte(request, analyte_name):
    pass


@login_required
def analyze(request):
    update_experiments_from_db(request)
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = newExperimentForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            expt = impact.Experiment()
            expt.db_load(db_name = db_name, experiment_id=request.session['experiment_id'])
            expt.info = form.cleaned_data
            experiment_id = expt.db_commit(db_name, overwrite_experiment_id=request.session['experiment_id'])
            update_experiments_from_db(request)
            return experimentSelect_analyze(request, experiment_id)
    # if a GET (or any other method) we'll create a blank form
    else:
        form = newExperimentForm()

        data = modifyMainPageSessionData(request, mainWindow = 'analyze')
        data['newExperimentForm'] = form

        return render(request, 'impact_cloud/analyze.html', data)

@login_required
def delete_experiment(request, experiment_id):
    impact.Experiment().db_delete(db_name, experiment_id)
    update_experiments_from_db(request)
    return analyze(request)

@login_required
def experimentSelect_analyze(request, experiment_id):
    strainInfo = impact.Experiment().get_strains_django(db_name, experiment_id)
    selectedExpt = impact.Experiment()
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

    data = modifyMainPageSessionData(request, experiment_id = int(experiment_id))
    data['newExperimentForm'] = form


    experiment = impact.Experiment()
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
    # print(replicate_info)
    return render(request, 'impact_cloud/analyze.html', data)