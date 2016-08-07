import copy
import sqlite3 as sql
import sys
import time

from PyQt4 import QtGui
from matplotlib import pyplot
from pyexcel_xlsx import get_data

import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt

import dill as pickle

from .TimePoint import TimePoint
from .AnalyteData import *
from .TrialIdentifier import *
from .SingleTrial import SingleTrial
from .ReplicateTrial import ReplicateTrial
from .Experiment import Experiment
from .Project import Project

from .QtGUI import *

__author__ = 'Naveen Venayak'

# If in the iPython environment, initialize notebook mode
try:
    temp = __IPYTHON__
except NameError:
    pass
else:
    import plotly
    plotly.offline.init_notebook_mode()

def init_db(db_name):
    """
    Initialize the database given a database file path.

    Parameters
    ----------
    db_name : str
        The path of the database, or name if it is in working directory
    """

    # Initialize database
    conn = sql.connect(db_name)
    c = conn.cursor()

    c.execute("""\
       CREATE TABLE IF NOT EXISTS experimentTable
       (experiment_id INTEGER PRIMARY KEY, import_date TEXT, experiment_title TEXT,
       experiment_start_date TEXT, experiment_end_date TEXT, primary_scientist_name TEXT,
       secondary_scientist_name TEXT, medium_base TEXT, medium_supplements TEXT, notes TEXT)
    """)

    c.execute("""\
       CREATE TABLE IF NOT EXISTS replicateTable
         (replicateID INTEGER PRIMARY KEY, experiment_id INT,
          strain_id TEXT, id_1 TEXT, id_2 TEXT, id_3 TEXT,
          FOREIGN KEY(experiment_id) REFERENCES experimentTable(experiment_id))
    """)

    for suffix in ['', '_avg', '_std']:
        c.execute("""\
           CREATE TABLE IF NOT EXISTS singleTrialTable""" + suffix + """
           (singleTrialID""" + suffix + """ INTEGER PRIMARY KEY, replicateID INT, replicate_id INT, yieldsDict BLOB,
           FOREIGN KEY(replicateID) REFERENCES replicateTable(replicateTable))
        """)

        c.execute("""\
           CREATE TABLE IF NOT EXISTS timeCourseTable""" + suffix + """
           (timeCourseID INTEGER PRIMARY KEY, singleTrial""" + suffix + """ID INTEGER,
           titerType TEXT, analyte_name TEXT, timeVec BLOB, dataVec BLOB, rate BLOB,
           FOREIGN KEY(singleTrial""" + suffix + """ID) REFERENCES singleTrialID(singleTrialTable""" + suffix + """))
        """)

    conn.commit()
    c.close()
    conn.close()


def printGenericTimeCourse_plotly(replicateTrialList=None, dbName=None, strainsToPlot=[], titersToPlot=[],
                                  secondary_y_axis_titers=None,
                                  output_type='html', stage_indices=None, stage=None,
                                  cl_scales=['10', 'qual', 'Paired'], colors=None,
                                  yieldFlag=False, titerFlag=True, endpointFlag=False, sortBy='strain_id',
                                  img_scale=1, fig_height=None, column_width_multiplier=400, number_of_columns=3,
                                  horizontal_spacing=0.2, vertical_spacing=0.4, row_height=300,
                                  format='web', single_subplot=False):
    """

    Parameters
    ----------
    replicateTrialList: ~class`titer`
        A list of replicate_id trials to be plotted
    dbName : str
        The name/path of the db if you will be loading data
    strainsToPlot : list
        A list of the strain identifiers, a concatenation of the strain_id+id_1+id_2
    titersToPlot : list
        A list of the titers to plot
    output_type : str
        The type of output (html, file, image, iPython)
    stage_indices : list of index pairs defining stages
        The indices of stages to be defined. This will be moved elsewhere
    stage : int
        The stage of interest (as defined in stage_indices)
    cl_scales : list of color scale identifiers
    colors : list of str indicating the color 'rgb(0, 0, 0)'
    yieldFlag : bool
        True to plot yield
    titerFlag : bool
        True to plot titer
    endpointFlag : bool
        True to plot endpoint, otherwise plot timecourse
    sortBy : str
        Identifier to plot by (strain_id, id_1, id_2, None)
    img_scale : int
        The output scale of the image
    fig_height : float
        The height of the figure
    column_width_multiplier : float
        The width of each column
    number_of_columns : int
        The number of columns
    horizontal_spacing : float
        The horizontal spacing between subplots
    vertical_spacing : float
        The vertical spacing between subplots
    row_height : float
        The height of a row in the plot
    format : str
        The format settings to use, the only option is poster
    """

    # Load plotly - will eventually move this to head
    from plotly import tools
    from plotly.offline import plot
    import plotly.graph_objs as go
    import plotly.plotly as py

    import math

    import colorlover as cl

    pts_per_hour = 1

    # Check for correct inputs
    if replicateTrialList is None and dbName is None:
        print('No replicate_id list or db_name')
        return 'No replicate_id list or db_name'
    if replicateTrialList is not None and dbName is not None:
        print('Supplied both a replicateTrialList and db_name')
        return 'Supplied both a replicateTrialList and db_name'

    # Load the data if a db was provided
    if dbName is not None:
        # Load data into replciate experiment object
        conn = sql.connect(dbName)
        c = conn.cursor()
        replicateTrialList = []
        for strain in strainsToPlot:
            tempReplicateTrial = ReplicateTrial()
            tempReplicateTrial.db_load(c=c, replicateID=strain)
            replicateTrialList.append(tempReplicateTrial)
        conn.close()

    # Switch the the replicate_id stages if we're looking at data for a specific stage
    if stage_indices is not None and stage is not None:
        newReplicateTrialList = []
        for replicateTrial in replicateTrialList:
            replicateTrial.calculate_stages(stage_indices=stage_indices)
            newReplicateTrialList.append(replicateTrial.stages[stage])
        replicateTrialList = newReplicateTrialList
    elif stage_indices is not None:
        print('Ignoring stages, no stage selected')
    elif stage is not None:
        print('Ignoring stages, no stage_indices provided')

    # Check if titers provided
    if titersToPlot == []:
        raise Exception('No titers defined to plot')

    if colors is None:
        color_scale = cl.scales[cl_scales[0]][cl_scales[1]][cl_scales[2]]
        # https://plot.ly/ipython-notebooks/color-scales/
        if len(replicateTrialList) > int(cl_scales[0]):
            colors = cl.interp(color_scale, 500)
            # Index the list
            colors = [colors[int(x)] for x in np.arange(0, 500, 500 / round(len(replicateTrialList)))]
        else:
            colors = color_scale
    # color_scale = cl.interp(color_scale, len(replicateTrialList))
    # Choose the subplot layout
    rows = math.ceil(len(titersToPlot) / number_of_columns)

    if fig_height is None:
        height = row_height * rows
    else:
        height = fig_height

    # Set default axes
    for titer in titersToPlot:
        if secondary_y_axis_titers is None:
            secondary_y_axis_titers = {}

        if titer not in secondary_y_axis_titers.keys():
            secondary_y_axis_titers[titer] = 'primary'

    supported_formats = ['poster', 'web']
    if format in supported_formats:
        if format == 'poster':
            chart_fonts = {'titlefont': {'size': 18, 'color': '#000000'},
                           'tickfont' : {'size': 18},
                           'color'    : '#000000'}
            layout_margin = {'b': 160, 'r': 100}
            axis_params = dict(linewidth=1.5, showline=True, ticks='outside',
                               showgrid=False, zeroline=False)
            bar_xaxis_params = dict(tickangle=-45, )
            legend_params = {'orientation': 'h', 'font': {'size': 10, 'color': '#000000'}}
        else:
            chart_fonts = {}
            layout_margin = {}
            axis_params = {}
            bar_xaxis_params = {}
            legend_params = {}
    else:
        raise Exception(format, ' is not a valid format, try one of ', supported_formats)

    # fig['layout'].update(height=height, legend={'orientation': 'h', 'font': {'size': 10, 'color': '#000000'}})


    if not (sortBy == 'product_in_legend' or single_subplot):
        fig = tools.make_subplots(rows=rows, cols=number_of_columns,
                                  horizontal_spacing=horizontal_spacing / number_of_columns,
                                  vertical_spacing=vertical_spacing / rows
                                  )
    else:
        fig = tools.make_subplots(rows=1, cols=2,
                                  horizontal_spacing=horizontal_spacing / number_of_columns,
                                  vertical_spacing=vertical_spacing / rows
                                  )

    # Only show the legend entry for the first time a strain is plotted, prevents duplicate entries
    if endpointFlag and sortBy:
        showlegend_flag = False
    else:
        showlegend_flag = True

    # An efficient sorting function that preserves order
    def f5(seq, idfun=None):
        # order preserving
        if idfun is None:
            def idfun(x): return x
        seen = {}
        result = []
        for item in seq:
            marker = idfun(item)
            # in old Python versions:
            # if seen.has_key(marker)
            # but in new ones:
            if marker in seen: continue
            seen[marker] = 1
            result.append(item)
        return result

    dataLabel = ''
    sort_by_flag = True
    sort_by_product_in_legend_flag = False
    pltNum = 0

    prepped_x = dict()
    prepped_y_avg = dict()
    prepped_y_std = dict()
    prepped_legendgroup = dict()
    for name in [replicate.runIdentifier.strain_id + '+' +
                         replicate.runIdentifier.id_1 + ',' +
                         replicate.runIdentifier.id_2 for replicate in replicateTrialList]:
        prepped_x[name] = []
        prepped_y_avg[name] = []
        prepped_y_std[name] = []
        prepped_legendgroup[name] = []

    for product in titersToPlot:
        if sortBy == 'product_in_legend' or single_subplot:
            if pltNum == 0:
                pltNum = 1
        else:
            pltNum += 1

        colorIndex = 0
        if endpointFlag:
            if (sortBy is not None and sortBy != 'product_in_legend') and sort_by_flag:
                uniques = f5([getattr(replicate.runIdentifier, sortBy) for replicate in replicateTrialList])
            else:
                if sortBy == 'product_in_legend':
                    sort_by_product_in_legend_flag = True

                uniques = ['']
                sortBy = 'strain_id'  # This is just a placeholder, it can be any attribute of RunIdentifier
                # just so the function call doesn't return an error
                sort_by_flag = False

            # if len(replicateTrialList) >= 6:
            #     colors = cl.interp(color_scale, len(uniques))
            if colors is None:
                colors = color_scale

            for i, unique in enumerate(uniques):
                x = unique
                if yieldFlag:
                    y_avg = [replicate.avg.yields[product] for replicate in replicateTrialList
                             if getattr(replicate.runIdentifier, sortBy) == unique or sort_by_flag is False]
                    y_std = [replicate.std.yields[product] for replicate in replicateTrialList
                             if getattr(replicate.runIdentifier, sortBy) == unique or sort_by_flag is False]
                    label = ' yield (g/g)'
                else:
                    y_avg = [replicate.avg.titerObjectDict[product].dataVec for replicate in replicateTrialList
                             if getattr(replicate.runIdentifier, sortBy) == unique or sort_by_flag is False]
                    y_std = [replicate.std.titerObjectDict[product].dataVec for replicate in replicateTrialList
                             if getattr(replicate.runIdentifier, sortBy) == unique or sort_by_flag is False]
                    label = ' titer (g/L)'

                legendgroup = ''
                for attribute in ['strain_id', 'id_1', 'id_2']:
                    if attribute != sortBy:
                        legendgroup += getattr(replicateTrialList[0].runIdentifier, attribute)

                if sort_by_flag:

                    legendgroup = unique

                    if sortBy == 'strain_id':
                        x = [replicate.runIdentifier.id_1 + ',' +
                             replicate.runIdentifier.id_2
                             for replicate in replicateTrialList
                             if getattr(replicate.runIdentifier, sortBy) == unique or sort_by_flag is False]
                    if sortBy == 'id_1':
                        x = [replicate.runIdentifier.strain_id + ',' +
                             replicate.runIdentifier.id_2
                             for replicate in replicateTrialList
                             if getattr(replicate.runIdentifier, sortBy) == unique or sort_by_flag is False]
                    if sortBy == 'id_2':
                        x = [replicate.runIdentifier.strain_id + '+' +
                             replicate.runIdentifier.id_1
                             for replicate in replicateTrialList
                             if getattr(replicate.runIdentifier, sortBy) == unique or sort_by_flag is False]

                else:
                    if sort_by_product_in_legend_flag:
                        x = [product for _ in replicateTrialList]
                        legendgroup = [replicate.runIdentifier.strain_id + '+' +
                                       replicate.runIdentifier.id_1 + ',' +
                                       replicate.runIdentifier.id_2 for replicate in replicateTrialList]
                    else:
                        legendgroup = None
                        x = [(replicate.runIdentifier.strain_id + '+' +
                              replicate.runIdentifier.id_1 +
                              replicate.runIdentifier.id_2).split('LMSE')[-1]
                             for replicate in replicateTrialList
                             if getattr(replicate.runIdentifier,
                                        sortBy) == unique or sort_by_flag is False]  # TODO remove the LMSE removal

                if sort_by_product_in_legend_flag:
                    showlegend_flag = True
                    for i, name in enumerate(legendgroup):
                        prepped_x[name].append(x[i])
                        prepped_y_avg[name].append(y_avg[i][-1])
                        prepped_y_std[name].append(y_std[i][-1])
                        prepped_legendgroup[name].append(legendgroup[i])
                else:
                    trace = go.Bar(x=x,
                                   y=[y[-1] for y in y_avg],
                                   error_y={
                                       'type'   : 'data',
                                       'array'  : [y[-1] for y in y_std],
                                       'visible': True,
                                       'color'  : colors[i]},
                                   marker={'color': colors[i]},
                                   showlegend=showlegend_flag,
                                   legendgroup=legendgroup,
                                   name=legendgroup)

                    if sort_by_product_in_legend_flag:
                        row = 1
                        col = 1
                    else:
                        row = math.ceil(pltNum / number_of_columns)
                        col = pltNum - (row - 1) * number_of_columns
                    if sort_by_flag:
                        fig['layout'].update(barmode='group')
                    print(row, ' ', col)
                    fig.append_trace(trace, row, col)
                    final_plot_number = pltNum

                    fig['layout']['xaxis' + str(pltNum)].update(**axis_params, **bar_xaxis_params, **chart_fonts)
                    fig['layout']['yaxis' + str(pltNum)].update(title=product + label, rangemode='nonnegative',
                                                                **axis_params, **chart_fonts)
                    fig['layout'].update(height=height, margin=layout_margin, showlegend=False)
                    showlegend_flag = False

        else:  # time course (not end point)
            for replicate in replicateTrialList:
                # Determine how many points should be plotted
                required_num_pts = replicate.t[-1] * pts_per_hour
                removePointFraction = int(len(replicate.t) / required_num_pts)

                if removePointFraction < 1:  removePointFraction = 1

                normalize_to = None

                # Get the correct data
                dataLabel = ''
                if yieldFlag:
                    if product != 'OD600':
                        dataLabel = '<br>yield (g/g)'
                    y_avg = replicate.avg.yields[product][::removePointFraction]
                    y_std = replicate.std.yields[product][::removePointFraction]
                elif titerFlag:
                    if product != 'OD600':
                        dataLabel = '<br>titer (g/L)'
                    y_avg = replicate.avg.titerObjectDict[product].dataVec[::removePointFraction]
                    y_std = replicate.std.titerObjectDict[product].dataVec[::removePointFraction]
                elif normalize_to is not None:
                    y_avg = replicate.avg.titerObjectDict[product].get_normalized_data(normalize_to)[
                            ::removePointFraction]
                    y_std = replicate.std.titerObjectDict[product].get_normalized_data(normalize_to)[
                            ::removePointFraction]

                # dataLabel = ''
                t = replicate.t[::removePointFraction]

                if product in replicate.avg.titerObjectDict:
                    trace = go.Scatter(x=t,
                                       y=y_avg,
                                       error_y={
                                           'type'   : 'data',
                                           'array'  : y_std,
                                           'visible': True,
                                           'color'  : colors[colorIndex]},
                                       mode='lines+markers',
                                       marker={
                                           'color': colors[colorIndex]},
                                       line={'color': colors[colorIndex]},
                                       showlegend=showlegend_flag,
                                       legendgroup=(replicate.runIdentifier.strain_id + '+' +
                                                    replicate.runIdentifier.id_1 +
                                                    replicate.runIdentifier.id_2).split('LMSE')[-1],
                                       name=(replicate.runIdentifier.strain_id + '+' +
                                             replicate.runIdentifier.id_1 +
                                             replicate.runIdentifier.id_2).split('LMSE')[-1])  # ,
                    #
                    # # Plot the fit curve
                    # if plotCurveFit and False \
                    #         and replicate_id.avg.titer_dict[product].runIdentifier.titerType in ['biomass', 'product'] \
                    #         and len(replicate_id.avg.titer_dict[product].rate.keys()) > 0:
                    #     # print(replicate_id.avg.titer_dict[product].rate)
                    #     trace = go.Scatter(x=np.linspace(min(t), max(t), 50),
                    #                        y=replicate_id.avg.titer_dict[product].returnCurveFitPoints(
                    #                            np.linspace(min(replicate_id.t), max(replicate_id.t), 50)),
                    #                        mode='line',
                    #                        name=replicate_id.runIdentifier.strain_id + '\t' +
                    #                             replicate_id.runIdentifier.id_1 + '\t' +
                    #                             replicate_id.runIdentifier.id_2,
                    #                        legendgroup=replicate_id.runIdentifier.strain_id + '\t' +
                    #                                    replicate_id.runIdentifier.id_1 + '\t' +
                    #                                    replicate_id.runIdentifier.id_2,
                    #                        line={'color': colors[colorIndex]})
                    #
                    #     if pltNum > 4:
                    #         row = 2
                    #         col = pltNum - 4
                    #     else:
                    #         row = 1
                    #         col = pltNum
                    #     fig.append_trace(trace, row, col)
                    #     trace = go.Scatter(x=t[::removePointFraction],
                    #                        y=replicate_id.avg.titer_dict[product].dataVec[::removePointFraction],
                    #                        error_y={
                    #                            'type'   : 'data',
                    #                            'array'  : replicate_id.std.titer_dict[product].dataVec[
                    #                                       ::removePointFraction],
                    #                            'visible': True,
                    #                            'color'  : colors[colorIndex]},
                    #                        mode='markers',
                    #                        marker={
                    #                            'color': colors[colorIndex]},
                    #                        legendgroup=replicate_id.runIdentifier.strain_id + '\t' +
                    #                                    replicate_id.runIdentifier.id_1 + '\t' +
                    #                                    replicate_id.runIdentifier.id_2,
                    #                        name=replicate_id.runIdentifier.strain_id + replicate_id.runIdentifier.id_1 + replicate_id.runIdentifier.id_2)
                    #     dataLabel = 'AnalyteData g/L'
                    # elif replicate_id.avg.titer_dict[
                    #     product].runIdentifier.titerType == 'product' and dataType == 'yields':
                    #     # Plot the data
                    #     trace = go.Scatter(x=t[::removePointFraction],
                    #                        y=replicate_id.avg.yields[product][::removePointFraction],
                    #                        error_y={
                    #                            'type'   : 'data',
                    #                            'array'  : replicate_id.std.yields[product][::removePointFraction],
                    #                            'visible': True,
                    #                            'color'  : colors[colorIndex]},
                    #                        mode='markers',
                    #                        marker={
                    #                            'color': colors[colorIndex]},
                    #                        legendgroup=replicate_id.runIdentifier.strain_id + '\t' +
                    #                                    replicate_id.runIdentifier.id_1 + '\t' +
                    #                                    replicate_id.runIdentifier.id_2,
                    #                        name=replicate_id.runIdentifier.strain_id + replicate_id.runIdentifier.id_1 + replicate_id.runIdentifier.id_2)
                    #     dataLabel = 'Yield mmol/mmol'
                    # else:
                    #     trace = go.Scatter(x=t[::removePointFraction],
                    #                        y=replicate_id.avg.titer_dict[product].dataVec[::removePointFraction],
                    #                        error_y={
                    #                            'type'   : 'data',
                    #                            'array'  : replicate_id.std.titer_dict[product].dataVec[
                    #                                       ::removePointFraction],
                    #                            'visible': True,
                    #                            'color'  : colors[colorIndex]},
                    #                        mode='lines+markers',
                    #                        marker={
                    #                            'color': colors[colorIndex]},
                    #                        line={'color': colors[colorIndex]},
                    #                        showlegend=showlegend_flag,
                    #                        legendgroup=replicate_id.runIdentifier.strain_id + '\t' +
                    #                                    replicate_id.runIdentifier.id_1 + '\t' +
                    #                                    replicate_id.runIdentifier.id_2,
                    #                        name=replicate_id.runIdentifier.strain_id + replicate_id.runIdentifier.id_1 + replicate_id.runIdentifier.id_2)  # ,
                    #     #                    label = '$\mu$ = '+'{:.2f}'.format(replicate_id.avg.OD.rate[1]) + ' $\pm$ ' + '{:.2f}'.format(replicate_id.std.OD.rate[1])+', n='+str(len(replicate_id.replicate_ids)-len(replicate_id.bad_replicates)))
                    #     dataLabel = 'AnalyteData g/L'

                    # Append the plot if it was created
                    if sortBy == 'product_in_legend' or single_subplot:
                        fig.append_trace(trace, 1, 1)
                    else:
                        row = math.ceil(pltNum / number_of_columns)
                        col = pltNum - (row - 1) * number_of_columns
                        fig.append_trace(trace, row, col)

                # Keep moving color index to keeps colors consistent across plots
                colorIndex += 1
                final_plot_number = pltNum

            # Set some plot aesthetics
            fig['layout']['xaxis' + str(pltNum)].update(title='Time (hours)', rangemode='tozero', **axis_params,
                                                        **chart_fonts)
            fig['layout']['yaxis' + str(pltNum)].update(title=product + ' ' + dataLabel, rangemode='tozero',
                                                        **axis_params, **chart_fonts)
            fig['layout'].update(height=height, legend=legend_params)
            showlegend_flag = False

            # else:
            #     raise Exception('No plot type selection (endpointFlag or yieldFlag must be True)')
    if sort_by_product_in_legend_flag:
        for name in prepped_x:
            trace = go.Bar(x=prepped_x[name],
                           y=prepped_y_avg[name],
                           error_y={
                               'type'   : 'data',
                               'array'  : prepped_y_std[name],
                               'visible': True},
                           showlegend=showlegend_flag,
                           legendgroup=prepped_legendgroup[name],
                           name=name)
            fig['layout'].update(barmode='group')
            fig.append_trace(trace, 1, 1)
            final_plot_number = pltNum

        fig['layout']['xaxis1'].update(**axis_params, **bar_xaxis_params, **chart_fonts)
        fig['layout']['yaxis1'].update(title=label, rangemode='nonnegative',
                                       **axis_params, **chart_fonts)
        fig['layout'].update(height=height, margin=layout_margin)

    # Clear the empty plots
    if not sort_by_product_in_legend_flag:
        for pltNum in range(final_plot_number + 1, number_of_columns * rows + 1):
            fig['layout']['xaxis' + str(pltNum)].update(showgrid=False, zeroline=False, showline=False, autotick=True,
                                                        ticks='', showticklabels=False)
            fig['layout']['yaxis' + str(pltNum)].update(showgrid=False, zeroline=False, showline=False, autotick=True,
                                                        ticks='', showticklabels=False)

    # Set the output type parameters, import the appropriate packages, and export
    if output_type == 'html':
        return plot(fig, show_link=False, output_type='div')
    elif output_type == 'file':
        plot(fig, show_link=True)
    elif output_type == 'iPython':
        from plotly.offline import iplot
        iplot(fig, show_link=False)
        return fig
    elif output_type == 'image':
        import random
        import string
        import plotly

        plotly.tools.set_credentials_file(username='nvenayak', api_key='8g4rh19bqj')
        fig['layout'].update(width=number_of_columns * column_width_multiplier)
        random_file_name = ''.join(random.choice(string.ascii_letters) for _ in range(10)) + '.png'
        py.image.save_as(fig, random_file_name, scale=img_scale)
        return random_file_name
