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

from .TimePoint import *
from .Titer import *
from .TrialIdentifier import *
from .SingleTrial import *
from .ReplicateTrial import *
from .Experiment import *
from .Project import *

from .QtGUI import *

__author__ = 'Naveen Venayak'

def init_db(db_name):
    """
    Initialize the database given a database file path.

    Parameters
    ----------
    db_name : str
        The path of the database, or name if it is in working directory
    """
    """
    Initiates the standard sqlite database

    Args:
        db_name (str): str database name
    """
    # Initialize database
    conn = sql.connect(db_name)
    c = conn.cursor()

    c.execute("""\
       CREATE TABLE IF NOT EXISTS experimentTable
       (experimentID INTEGER PRIMARY KEY, importDate TEXT, experimentTitle TEXT,
       runStartDate TEXT, runEndDate TEXT, principalScientistName TEXT,
       secondaryScientistName TEXT, mediumBase TEXT, mediumSupplements TEXT, notes TEXT)
    """)

    c.execute("""\
       CREATE TABLE IF NOT EXISTS replicateTable
         (replicateID INTEGER PRIMARY KEY, experimentID INT,
          strainID TEXT, identifier1 TEXT, identifier2 TEXT, identifier3 TEXT,
          FOREIGN KEY(experimentID) REFERENCES experimentTable(experimentID))
    """)

    for suffix in ['', '_avg', '_std']:
        c.execute("""\
           CREATE TABLE IF NOT EXISTS singleTrialTable""" + suffix + """
           (singleTrialID""" + suffix + """ INTEGER PRIMARY KEY, replicateID INT, replicate INT, yieldsDict BLOB,
           FOREIGN KEY(replicateID) REFERENCES replicateTable(replicateTable))
        """)

        c.execute("""\
           CREATE TABLE IF NOT EXISTS timeCourseTable""" + suffix + """
           (timeCourseID INTEGER PRIMARY KEY, singleTrial""" + suffix + """ID INTEGER,
           titerType TEXT, titerName TEXT, timeVec BLOB, dataVec BLOB, rate BLOB,
           FOREIGN KEY(singleTrial""" + suffix + """ID) REFERENCES singleTrialID(singleTrialTable""" + suffix + """))
        """)

    conn.commit()
    c.close()
    conn.close()

def printGenericTimeCourse_plotly(replicateTrialList=None, dbName=None, strainsToPlot=[], titersToPlot=[],
                                  shadeErrorRegion=False, showGrowthRates=True, plotCurveFit=True, dataType='raw',
                                  output_type='html', stage_indices = None):
    # Load plotly - will eventually move this to head
    from plotly import tools
    from plotly.offline import plot
    import plotly.graph_objs as go

    import colorlover as cl

    pts_per_hour = 1

    if replicateTrialList is None and dbName is None:
        print('No replicate list or dbName')
        return 'No replicate list or dbName'

    if replicateTrialList is not None and dbName is not None:
        print('Supplied both a replicateTrialList and dbName')
        return 'Supplied both a replicateTrialList and dbName'

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

    newReplicateTrialList = []
    for replicateTrial in replicateTrialList:
        replicateTrial.calculate_stages(stage_indices=[[0, 4], [5, 8]])
        newReplicateTrialList.append(replicateTrial.stages[1])
    replicateTrialList = newReplicateTrialList

    # Plot all product titers if none specified
    if titersToPlot == []:
        raise Exception('No titers defined to plot')
    print(len(replicateTrialList))
    # https://plot.ly/ipython-notebooks/color-scales/
    colors = cl.scales['8']['qual']['Dark2']
    if len(replicateTrialList) >= 6:
        colors = cl.interp(colors, len(replicateTrialList))

    # Choose the subplot layout
    if len(titersToPlot) == 1:
        rows = 1
        fig = tools.make_subplots(rows=1, cols=1)
        height = 400
    elif len(titersToPlot) < 5:
        rows = 1
        fig = tools.make_subplots(rows=1, cols=len(titersToPlot))
        height = 400
    elif len(titersToPlot) < 9:
        rows = 2
        fig = tools.make_subplots(rows=2, cols=4)
        height = 800
    else:
        raise Exception("Unimplemented Functionality")

    pltNum = 0
    showlegend_flag = True
    for product in titersToPlot:
        pltNum += 1

        # Plotting yield, titer or productivity?
        yieldFlag = True
        titerFlag = True
        productivityFlag = False
        endpoint_flag = True
        sortBy = 'strainID'

        trace = []
        colorIndex = 0

        if endpoint_flag:
            uniques = list(set(
                [getattr(replicate.runIdentifier, sortBy) for replicate in replicateTrialList]
            ))
            uniques.sort()
            print(uniques)
            print(colors)
            colors = cl.scales['8']['qual']['Dark2']
            if len(replicateTrialList) >= 6:
                colors = cl.interp(colors, len(uniques))

            for i, unique in enumerate(uniques):
                x = unique
                if yieldFlag:
                    y_avg = [replicate.avg.yields[product] for replicate in
                             replicateTrialList
                             if getattr(replicate.runIdentifier, sortBy) == unique]
                    print(y_avg)
                    y_std = [replicate.std.yields[product] for replicate in
                             replicateTrialList
                             if getattr(replicate.runIdentifier, sortBy) == unique]
                else:
                    y_avg = [replicate.avg.titerObjectDict[product].dataVec for replicate in replicateTrialList
                             if getattr(replicate.runIdentifier, sortBy) == unique]
                    y_std = [replicate.std.titerObjectDict[product].dataVec for replicate in replicateTrialList
                             if getattr(replicate.runIdentifier, sortBy) == unique]

                print('x:',x)
                print('y[-1]',[y[-1] for y in y_avg])
                trace = go.Bar(x= x,
                               y = [y[-1] for y in y_avg],
                               error_y={
                                   'type'   : 'data',
                                   'array'  : [y[-1] for y in y_std],
                                   'visible': True,
                                   'color'  : colors[i]},
                               marker={'color': colors[i]},
                               showlegend=showlegend_flag,
                               legendgroup=[replicate.runIdentifier.strainID + '\t' +
                                            replicate.runIdentifier.identifier1 + '\t' +
                                            replicate.runIdentifier.identifier2 for replicate in replicateTrialList if getattr(replicate.runIdentifier, sortBy) == unique],
                               name=[
                                   replicate.runIdentifier.strainID + replicate.runIdentifier.identifier1 + replicate.runIdentifier.identifier2
                                   for replicate in replicateTrialList if getattr(replicate.runIdentifier, sortBy) == unique]
                               )
                if pltNum > 4:
                    row = 2
                    col = pltNum - 4
                else:
                    row = 1
                    col = pltNum
                fig.append_trace(trace, row, col)
            fig['layout'].update(barmode='group')
            fig['layout']['xaxis' + str(pltNum)].update(title='Time (hours)')
            fig['layout']['yaxis' + str(pltNum)].update(title=product)
            showlegend_flag = False

        else:
            for replicate in replicateTrialList:
                # Determine how many points should be plotted
                required_num_pts = replicate.t[-1] * pts_per_hour
                removePointFraction = int(len(replicate.t) / required_num_pts)

                if removePointFraction < 1:  removePointFraction = 1

                # Get the correct data
                if yieldFlag:
                    y_avg = replicate.avg.yields[product][::removePointFraction]
                    y_std = replicate.std.yields[product][::removePointFraction]
                if titerFlag:
                    y_avg = replicate.avg.titerObjectDict[product].dataVec[::removePointFraction]
                    y_std = replicate.std.titerObjectDict[product].dataVec[::removePointFraction]

                dataLabel = ''
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
                                       legendgroup=replicate.runIdentifier.strainID + '\t' +
                                                   replicate.runIdentifier.identifier1 + '\t' +
                                                   replicate.runIdentifier.identifier2,
                                       name=replicate.runIdentifier.strainID + replicate.runIdentifier.identifier1 + replicate.runIdentifier.identifier2)  # ,
                    #
                    # # Plot the fit curve
                    # if plotCurveFit and False \
                    #         and replicate.avg.titerObjectDict[product].runIdentifier.titerType in ['biomass', 'product'] \
                    #         and len(replicate.avg.titerObjectDict[product].rate.keys()) > 0:
                    #     # print(replicate.avg.titerObjectDict[product].rate)
                    #     trace = go.Scatter(x=np.linspace(min(t), max(t), 50),
                    #                        y=replicate.avg.titerObjectDict[product].returnCurveFitPoints(
                    #                            np.linspace(min(replicate.t), max(replicate.t), 50)),
                    #                        mode='line',
                    #                        name=replicate.runIdentifier.strainID + '\t' +
                    #                             replicate.runIdentifier.identifier1 + '\t' +
                    #                             replicate.runIdentifier.identifier2,
                    #                        legendgroup=replicate.runIdentifier.strainID + '\t' +
                    #                                    replicate.runIdentifier.identifier1 + '\t' +
                    #                                    replicate.runIdentifier.identifier2,
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
                    #                        y=replicate.avg.titerObjectDict[product].dataVec[::removePointFraction],
                    #                        error_y={
                    #                            'type'   : 'data',
                    #                            'array'  : replicate.std.titerObjectDict[product].dataVec[
                    #                                       ::removePointFraction],
                    #                            'visible': True,
                    #                            'color'  : colors[colorIndex]},
                    #                        mode='markers',
                    #                        marker={
                    #                            'color': colors[colorIndex]},
                    #                        legendgroup=replicate.runIdentifier.strainID + '\t' +
                    #                                    replicate.runIdentifier.identifier1 + '\t' +
                    #                                    replicate.runIdentifier.identifier2,
                    #                        name=replicate.runIdentifier.strainID + replicate.runIdentifier.identifier1 + replicate.runIdentifier.identifier2)
                    #     dataLabel = 'Titer g/L'
                    # elif replicate.avg.titerObjectDict[
                    #     product].runIdentifier.titerType == 'product' and dataType == 'yields':
                    #     # Plot the data
                    #     trace = go.Scatter(x=t[::removePointFraction],
                    #                        y=replicate.avg.yields[product][::removePointFraction],
                    #                        error_y={
                    #                            'type'   : 'data',
                    #                            'array'  : replicate.std.yields[product][::removePointFraction],
                    #                            'visible': True,
                    #                            'color'  : colors[colorIndex]},
                    #                        mode='markers',
                    #                        marker={
                    #                            'color': colors[colorIndex]},
                    #                        legendgroup=replicate.runIdentifier.strainID + '\t' +
                    #                                    replicate.runIdentifier.identifier1 + '\t' +
                    #                                    replicate.runIdentifier.identifier2,
                    #                        name=replicate.runIdentifier.strainID + replicate.runIdentifier.identifier1 + replicate.runIdentifier.identifier2)
                    #     dataLabel = 'Yield mmol/mmol'
                    # else:
                    #     trace = go.Scatter(x=t[::removePointFraction],
                    #                        y=replicate.avg.titerObjectDict[product].dataVec[::removePointFraction],
                    #                        error_y={
                    #                            'type'   : 'data',
                    #                            'array'  : replicate.std.titerObjectDict[product].dataVec[
                    #                                       ::removePointFraction],
                    #                            'visible': True,
                    #                            'color'  : colors[colorIndex]},
                    #                        mode='lines+markers',
                    #                        marker={
                    #                            'color': colors[colorIndex]},
                    #                        line={'color': colors[colorIndex]},
                    #                        showlegend=showlegend_flag,
                    #                        legendgroup=replicate.runIdentifier.strainID + '\t' +
                    #                                    replicate.runIdentifier.identifier1 + '\t' +
                    #                                    replicate.runIdentifier.identifier2,
                    #                        name=replicate.runIdentifier.strainID + replicate.runIdentifier.identifier1 + replicate.runIdentifier.identifier2)  # ,
                    #     #                    label = '$\mu$ = '+'{:.2f}'.format(replicate.avg.OD.rate[1]) + ' $\pm$ ' + '{:.2f}'.format(replicate.std.OD.rate[1])+', n='+str(len(replicate.replicate_ids)-len(replicate.bad_replicates)))
                    #     dataLabel = 'Titer g/L'
                    # Append the plot if it was created
                    if pltNum > 4:
                        row = 2
                        col = pltNum - 4
                    else:
                        row = 1
                        col = pltNum
                    fig.append_trace(trace, row, col)
                # Keep moving color index to keeps colors consistent across plots
                colorIndex += 1
            # Set some plot aesthetics
            fig['layout']['xaxis' + str(pltNum)].update(title='Time (hours)')
            fig['layout']['yaxis' + str(pltNum)].update(title=product + ' ' + dataLabel)
            fig['layout'].update(height=height)
            showlegend_flag = False
    # fig['layout'].update = go.Figure(data=trace, layout=layout)
    if output_type == 'html':
        return plot(fig, show_link=False, output_type='div')
    elif output_type == 'file':
        plot(fig, show_link=True)
    elif output_type == 'iPython':
        from plotly.offline import iplot
        iplot(fig, show_link=False)
        return fig


