from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from impact.settings import db_name
import impact
from impact import printGenericTimeCourse_plotly

from .tools import update_experiments_from_db, modifyMainPageSessionData
from .plot import updateFigure


@login_required
def download_plot(request):
    """
    Function to generate a figure with a very high ppi (i.e. for posters) for download, this required hard-coded
    api key for plotly. Similar functionality can be obtained by exporting to plotly for edits.

    Parameters
    ----------
    request

    Returns
    -------
    HttpResponse : returns the image_data as the response
    """
    file_name = printGenericTimeCourse_plotly(dbName=db_name,
                                         strainsToPlot=[strain['replicateID'] for strain in
                                                        request.session['selectedStrainsInfo']],
                                         titersToPlot=request.session['selectedTiters'],
                                         output_type='image', format='poster',img_scale=10,
                                         **request.session['prepared_plot_options']
                                         )
    image_data = open(file_name,'rb').read()
    return HttpResponse(image_data, content_type="image/png")

@login_required
def selectMainWindow(request, mainWindowSelection):
    update_experiments_from_db(request)
    if mainWindowSelection == 'plot':
        request.session['mainWindow'] = mainWindowSelection
        experiment = impact.Experiment()
        experiment.db_load(db_name, 1)
        updateFigure(request)
        data = modifyMainPageSessionData(request)
    elif mainWindowSelection == 'rawData':
        request.session['mainWindow'] = mainWindowSelection
        data = modifyMainPageSessionData(request)
    else:
        data = modifyMainPageSessionData(request)
    return render(request, 'impact_cloud/plot.html',data)