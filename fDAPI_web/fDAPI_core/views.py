from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
# from forms import newExperimentForm
from .forms import newExperimentForm

from django.contrib.auth.views import *
# from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required



import sys
import os

# Add the toolbox path
sys.path.append(os.path.join(os.path.dirname(__file__),'../../'))
import fDAPI

# Set the default dbName, stored in the root directory
dbName = os.path.join(os.path.dirname(__file__),"../../default_fDAPI_db.sqlite3")



# Create your views here.
def index(request):
    return render(request,'fDAPI_core/login.html')

def newExperiment(request):
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

    return render(request, 'fDAPI_core/newExperiment.html', {'newExperimentForm': form})


def createAccount(request):
    from django.contrib.auth.models import User

    user = User.objects.create_user(request.POST['username'], request.POST['email'], request.POST['password'])
    pass

def register(request):
    return HttpResponse('No registration page created')

@login_required()
def core(request):
    exptInfo = fDAPI.Project().getAllExperimentInfo_django(dbName)
    data = modifyMainPageSessionData(request, exptInfo = exptInfo)

    return render(request, 'fDAPI_core/home.html', data)

# @login_required
def experimentSelect(request, experimentID):
    strainInfo = fDAPI.Experiment().getAllStrains_django(dbName,experimentID)
    request.session['strainInfo'] = strainInfo

    # Determine the unique identifiers for use in the sorting dropdown
    uniqueIDs = dict()
    for key in ['strainID','identifier1','identifier2']:
        uniqueIDs[key] = sorted(set([strain[key] for strain in strainInfo]))

    data = modifyMainPageSessionData(request, uniqueIDs = uniqueIDs)
    return render(request, 'fDAPI_core/home.html', data)

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
        data = modifyMainPageSessionData(request, titerNames = fDAPI.Project().getTitersSelectedStrains_django(dbName, data['selectedStrainsInfo']))
    else:
        return HttpResponse('Expected POST for selectStrains')
    return render(request, 'fDAPI_core/home.html',data)

def removeStrains(request):
    if request.method == 'POST':
        request.session['selectedStrainsInfo'] = [strain for strain in request.session['selectedStrainsInfo'] if str(strain['replicateID']) not in request.POST.keys()]

        data = updateFigure(request)
        return render(request, 'fDAPI_core/home.html',data)
    else:
        return HttpResponse('Expected POST data for /selectTiters/')

def clearData(request):
    data = modifyMainPageSessionData(request, selectedStrainsInfo = [])

    return render(request, 'fDAPI_core/home.html', data)

def selectTiters(request):
    if request.method == 'POST':
        modifyMainPageSessionData(request, selectedTiters = [titer for titer in request.session['titerNames'] if titer in request.POST.keys()])
        data = updateFigure(request)
        return render(request, 'fDAPI_core/home.html', data)
    else:
        return HttpResponse('Expected POST data for /selectTiters/')


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


        data = updateFigure(request)
        return render(request, 'fDAPI_core/home.html',data)
    else:
        return HttpResponse('Expected POST')

def selectMainWindow(request, mainWindowSelection):
    if mainWindowSelection == 'plot':
        request.session['mainWindow'] = mainWindowSelection
        experiment = fDAPI.Experiment()
        experiment.loadFromDB(dbName,1)
        updateFigure(request)
        data = modifyMainPageSessionData(request)
    elif mainWindowSelection == 'rawData':
        request.session['mainWindow'] = mainWindowSelection
        data = modifyMainPageSessionData(request)
    else:
        data = modifyMainPageSessionData(request)
    return render(request, 'fDAPI_core/home.html',data)

def updateFigure(request):
    if 'mainWindow' in request.session.keys():
        if request.session['mainWindow'] == 'plot' and\
                len(request.session['selectedStrainsInfo']) > 0 and\
                len(request.session['selectedTiters']) > 0:
            data = modifyMainPageSessionData(request, plotlyCode = fDAPI.printGenericTimeCourse_plotly(dbName = dbName,
                                                                                                         strainsToPlot = [strain['replicateID'] for strain in request.session['selectedStrainsInfo']],
                                                                                                         titersToPlot = request.session['selectedTiters'],
                                                                                                         dataType = 'raw'
                                                                                                         ))
        else:
             data = modifyMainPageSessionData(request)
    else:
         data = modifyMainPageSessionData(request)
    return data


def modifyMainPageSessionData(request, **kwargs):
    data = dict()
    for key in ['strainInfo','exptInfo','selectedStrainsInfo','mainWindow', 'plotlyCode',
                'titerNames','strainsToPlot','uniqueIDs','selectedTiters']:
        if key in kwargs:
            data[key] = kwargs[key]
            request.session[key] = kwargs[key]
        elif key in request.session.keys():
            data[key] = request.session[key]
        else:
            data[key] = []
            request.session[key] = []

    return data

def input(request):
    return render(request, 'fDAPI_core/input.html')

def inputData(request):
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
        print(firstEmptyRowIndex)
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
            cleanedData = []
            for i, row in enumerate(truncData):
                # First row should be one blank and a time vector
                if i == 0:
                    print(row[1:])
                    print('printed first row')
                    cleanedData.append(['']+[float(elem) for elem in row[1:]])
                else:
                    cleanedRow = []
                    for j, col in enumerate(row):
                        if j == 0:
                            cleanedRow.append(col)
                        else:
                            cleanedRow.append(float(col))
                    cleanedData.append(cleanedRow)
            # Load the data into the model
            expt = fDAPI.Experiment()

            expt.parseRawData('NV_OD', data = cleanedData) # Convert strings to floats


    else:
        print('EXPECTED POST')



def setupInputLayout():
    pass
    # For NV_OD input type