'''
Written by: Naveen Venyak
Date:       October, 2015

This is the main data object container. Almost all functionality is contained here.
'''

__author__ = 'Naveen Venayak'

import sqlite3 as sql
import time
import datetime
import copy
import sys
import plotly as py

import numpy as np
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from lmfit import Model
from pyexcel_xlsx import get_data
from PyQt4 import QtGui, QtCore

import dill as pickle
from .QtGUI import *



def initDB(dbName):
    # SQLite stuff
    # Initialize database
    conn = sql.connect(dbName)
    c = conn.cursor()

    c.execute("""\
       CREATE TABLE IF NOT EXISTS experimentTable
       (experimentID INTEGER PRIMARY KEY, importDate TEXT, experimentTitle TEXT, runStartDate TEXT, runEndDate TEXT, principalScientistName TEXT,
       secondaryScientistName TEXT, mediumBase TEXT, mediumSupplements TEXT, notes TEXT)
    """)

    c.execute("""\
       CREATE TABLE IF NOT EXISTS replicateTable
         (replicateID INTEGER PRIMARY KEY, experimentID INT,
          strainID TEXT, identifier1 TEXT, identifier2 TEXT, identifier3 TEXT,
          FOREIGN KEY(experimentID) REFERENCES experimentTable(experimentID))
    """)

    for suffix in ['','_avg','_std']:
        c.execute("""\
           CREATE TABLE IF NOT EXISTS singleTrialTable"""+suffix+"""
           (singleTrialID"""+suffix+""" INTEGER PRIMARY KEY, replicateID INT, replicate INT, yieldsDict BLOB,
           FOREIGN KEY(replicateID) REFERENCES replicateTable(replicateTable))
        """)

        c.execute("""\
           CREATE TABLE IF NOT EXISTS timeCourseTable"""+suffix+"""
           (timeCourseID INTEGER PRIMARY KEY, singleTrial"""+suffix+"""ID INTEGER,
           titerType TEXT, titerName TEXT, timeVec BLOB, dataVec BLOB, rate BLOB,
           FOREIGN KEY(singleTrial"""+suffix+"""ID) REFERENCES singleTrialID(singleTrialTable"""+suffix+"""))
        """)

    conn.commit()
    c.close()
    conn.close()

def generateSyntheticData(y0, t, model, biomass_keys, substrate_keys, product_keys, noise = 0, plot = True):
    import numpy as np
    from scipy.integrate import odeint
    import matplotlib.pyplot as plt

    # Let's assign the data to these variables
    biomass_flux = []
    biomass_flux.append(model.solution.x_dict[biomass_keys[0]])

    substrate_flux = []
    substrate_flux.append(model.solution.x_dict[substrate_keys[0]])

    product_flux = [model.solution.x_dict[key] for key in product_keys]

    exchange_keys = biomass_keys + substrate_keys + product_keys

    # Now, let's build our model for the dFBA
    def dFBA_functions(y, t, biomass_flux, substrate_flux, product_flux):
        # Append biomass, substrate and products in one list
        exchange_reactions = biomass_flux + substrate_flux + product_flux
                                # y[0]           y[1]
        dydt = []
        for exchange_reaction in exchange_reactions:
            if y[1] > 0: # If there is substrate
                dydt.append(exchange_reaction*y[0])
            else: #If there is not substrate
                dydt.append(0)
        return dydt

    # Now let's generate the data
    sol = odeint(dFBA_functions, y0, t, args=([flux*np.random.uniform(1-noise,1+noise) for flux in biomass_flux],
                                          [flux*np.random.uniform(1-noise,1+noise) for flux in substrate_flux],
                                          [flux*np.random.uniform(1-noise,1+noise) for flux in product_flux]))

    dFBA_profile = {key: [row[i] for row in sol] for i, key in enumerate(exchange_keys)}

    if plot == True:
        plt.figure(figsize=[12,6])
        for key in exchange_keys:
            plt.plot(t, dFBA_profile[key])
        plt.ylim([0,250])
        plt.legend(exchange_keys, loc=2)

    return dFBA_profile

class Project(object):
    """
    """

    colorMap = 'Set3'

    def __init__(self):
        self.dbName = 'defaultProjectDatabase.db'
        try:
            print('tried it')
            self.experimentList = pickle.load(open('testpickle.p','rb'))
        except Exception as e:
            print('caught it')
            self.experimentList = []

        print('length of experimentList on fileOpen/Create: ',self.experimentList)

        conn = sql.connect(self.dbName)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS replicateExperiment (experimentID INT, strainID TEXT, identifier1 TEXT, identifier2 TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS experiments (dateAdded TEXT, experimentDate TEXT, experimentDescription TEXT)")
        conn.commit()
        c.close()
        conn.close()
        # print(experimentDataRaw[0])
        # test = pickle.loads(str(experimentDataRaw[0]))
        # self.experimentData = [pickle.loads(str(experimentDataRaw[i])) for i in range(len(experimentDataRaw))]

        # for experiment in self.experimentDataRaw
        #     self.experimentData = pickle.loads(self.experimentDataRaw)
        # print([self.experimentDate, self.experimentName])
        # c.close()
        # conn.close()

    def newExperiment(self, dateStamp, description,rawData):
        experiment = Experiment()
        experiment.parseRawData(rawData[1],fileName = rawData[0])
        # conn = sql.connect('defaultProjectDatabase.db')
        # c = conn.cursor()
        # preppedData = sql.Binary(pickle.dumps(experiment,pickle.HIGHEST_PROTOCOL))
        # c.execute("INSERT INTO experimentTable(datestamp,description,data) VALUES(?, ?, ?)",(dateStamp,description,preppedData))
        # conn.commit()
        # c.close()
        # conn.close()
        self.experimentList.append([dateStamp, description, experiment])

        # Build tables for each of the lists within experimentList
        conn = sql.connect(self.dbName)
        c = conn.cursor()

        c.execute("INSERT INTO experiments (dateAdded, experimentDate, experimentDescription) VALUES (?,?,?)",
                  (datetime.datetime.now().strftime("%Y%m%d %H:%M"),dateStamp,description))

        for attrName, tableName in zip(['timePointList','titerObjectDict','singleExperimentObjectDict','replicateExperimentObjectDict'],
                                       ['TimePoint', 'Titer', 'singleExperiment', 'replicateExperiment']):
            if attrName == 'replicateExperimentObjectDict':
                for key in getattr(experiment,attrName):
                    c.execute("INSERT INTO replicateExperiment (experimentID, strainID, identifier1, identifier2) VALUES (?, ?,?,?)",
                              (len(self.experimentList),
                               getattr(experiment,attrName)[key].runIdentifier.strainID,
                               getattr(experiment,attrName)[key].runIdentifier.identifier1,
                               getattr(experiment,attrName)[key].runIdentifier.identifier2)
                              )


            # if attrName == 'singleExperimentObject'

            # if attrName == 'timePointList':
            #     for TimePoint in getattr(experiment,attrName):
            #         c.execute("INSERT INTO ? ( VALUES (?,?,?,?)")
            # for key in getattr(experiment,attrName):
            #     getattr(experiment,attrName)[key]

        c.close()
        conn.commit()
        conn.close()
        # self.timePointList = []#dict()
        # self.titerObjectDict = dict()
        # self.singleExperimentObjectDict = dict()
        # self.replicateExperimentObjectDict = dict()

            # SQLite stuff
            # Initialize database
            # conn = sql.connect('temptSQLite3db.db')
            # c = conn.cursor()
            # c.execute("""INSERT INTO timeCourseTable VALUES (?,?,?,?,?,?,?,?,?)""" ,
            #           (datetime.datetime.now().strftime("%Y%m%d %H:%M"),
            #           self.RunIdentifier.strainID,
            #           self.RunIdentifier.identifier1,
            #           self.RunIdentifier.identifier2,
            #           self.RunIdentifier.replicate,
            #           self.RunIdentifier.time,
            #           self.RunIdentifier.titerName,
            #           self.RunIdentifier.titerType))
            # conn.commit()
            # c.close()
            # conn.close()

        # c.execute(
        #     "I"
        # )



        pickle.dump(self.experimentList,open('testpickle.p','wb'))

    def getExperiments(self):
        print('There are ',len(self.experimentList),' experiments')
        # print(self.experimentList)
        conn = sql.connect(self.dbName)
        c = conn.cursor()
        c.execute("SELECT rowid, experimentDate, experimentDescription FROM experiments")
        data = c.fetchall()
        c.close()
        conn.close()
        return data

        # return [[row[0] for row in self.experimentList],[row[1] for row in self.experimentList]]
        # return [[experimentList.]]
        # conn = sql.connect('defaultProjectDatabase.db')
        # c = conn.cursor()
        # c.execute("SELECT datestamp, description FROM experimentTable")
        # data = c.fetchall()
        # c.close()
        # conn.close()
        # return data

    def getAllExperimentInfo_django(self, dbName):
        conn = sql.connect(dbName)
        c = conn.cursor()
        c.execute("SELECT * FROM experimentTable")
        exptDescription = []
        for row in c.fetchall():
            exptDescription.append({key: data for data, key in zip(row,[elem[0] for elem in c.description])})

        c.close()
        conn.close()
        return exptDescription

    def getStrainInfo_django(self):
        conn = sql.connect(dbName)
        c = conn.cursor()
        c.execute("SELECT experimentID, strainID, identifier1, identifier2 FROM replicateExperiment order by experimentID ASC, strainID ASC, identifier1 ASC, identifier2 ASC")
        data = list(c.fetchall())
        dataList = []
        for row in data:
            dataList.append(list(row))
        c.close()
        conn.close()
        # print(dataList)
        # print(self.experimentList[row[0]-1])
        for row in dataList:
            row.append(self.experimentList[row[0]-1][2].replicateExperimentObjectDict[row[1]+row[2]+row[3]])
        # print(dataList)
        return dataList

    def getAllTiterNames(self):
        titerNames = []
        for experiment in self.experimentList:
            for key in experiment[2].replicateExperimentObjectDict:
                for singleExperiment in experiment[2].replicateExperimentObjectDict[key].singleTrialList:
                    for product in singleExperiment.products:
                       titerNames.append(product)

                    if singleExperiment.OD != None:
                        titerNames.append('OD')
        uniqueTiterNames = set(titerNames)
        return uniqueTiterNames

    def getTitersSelectedStrains_django(self, dbName, selectedStrainsInfo):
        conn = sql.connect(dbName)
        c = conn.cursor()
        # Determine number of selected strains and create a string of ?s for DB query
        replicateIDs = [selectedStrain['replicateID'] for selectedStrain in selectedStrainsInfo]
        # c.execute("""SELECT singleTrialID_avg FROM singleTrialTable_avg
        # WHERE replicateID IN ("""+'?,'*len(replicateIDs)-1+"""?))""",tuple(replicateIDs))
        # for row in c.fetchall():


        c.execute("""SELECT titerName FROM timeCourseTable_avg WHERE singleTrial_avgID IN  ("""+'?, '*(len(replicateIDs)-1)+""" ?)"""
                  ,tuple(replicateIDs))
        titerList = [row[0] for row in c.fetchall()]
        conn.close()

        uniqueTiters = list(set(titerList))


        return uniqueTiters

    def getAllStrainsByIDSQL(self, experiment_id):
        conn = sql.connect(self.dbName)
        c = conn.cursor()
        experiment_id += 1
        c.execute("SELECT strainID, identifier1, identifier2 FROM replicateExperiment  WHERE (experimentID = ?)",(experiment_id,))
        data = c.fetchall()
        c.close()
        conn.close()
        return data

    def getReplicateExperimentFromID(self, id):
        conn = sql.connect(self.dbName)
        c = conn.cursor()
        c.execute("SELECT experimentID, strainID, identifier1, identifier2 FROM replicateExperiment WHERE (rowid = ?)",(id,))
        data = c.fetchall()
        c.close()
        conn.close()
        a = [data[0], data[1]+data[2]+data[3]]
        return a

    def plottingGUI(self):
        app = QtGui.QApplication(sys.argv)
        app.setApplicationName('fDAPI Plotting Interface')

        main = mainWindow(self)
        main.showMaximized()

        sys.exit(app.exec_())

    def plottingGUI2(self):
        app = QtGui.QApplication(sys.argv)
        app.setApplicationName('fDAPI Plotting Interface')
        MainWindow = QtGui.QMainWindow()
        ui = Ui_MainWindow()
        ui.setupUi(MainWindow, Project)
        MainWindow.showMaximized()

        sys.exit(app.exec_())

    def printGenericTimeCourse(self, figHandle = [], strainsToPlot=[], titersToPlot=[], removePointFraction=6, shadeErrorRegion=False, showGrowthRates=True, plotCurveFit=True ):
        if figHandle == []:
            figHandle = plt.figure(figsize=(12,8))

        figHandle.set_facecolor('w')

        # if strainsToPlot == []:
        #     strainsToPlot = self.getAllStrainNames()
            # replicateExperimentObjects
        # Plot all product titers if none specified TODO: Add an option to plot OD as well
        if titersToPlot == []:
            titersToPlot = ['OD']#self.getAllTiters()
        else:
            # Check if titer exists for each strainToPlot
            titersToPlotPerStrain = []
            for row in strainsToPlot:
                temp = []
                for i, product in enumerate(titersToPlot):
                    if product in row[5].singleTrialList[0].products:
                        temp.append(True)
                    else:
                        temp.append(False)
                titersToPlotPerStrain.append(temp)
        titerNames = []
        for experiment in self.experimentList:
            for key in experiment[2].replicateExperimentObjectDict:
                for singleExperiment in experiment[2].replicateExperimentObjectDict[key].singleTrialList:
                    for product in singleExperiment.products:
                       titerNames.append(product)

                    if singleExperiment.OD != None:
                        titerNames.append('OD')
        uniqueTiterNames = set(titerNames)

        # print(strainsToPlot,titersToPlot)

        # Determine optimal figure size
        if len(titersToPlot) == 1:
            figureSize = (12,6)
        if len(titersToPlot) > 1:
            figureSize = (12,3.5)
        if len(titersToPlot) > 4:
            figureSize = (12,7)

        if plotCurveFit==True:
            plotSymbol = 'o'
        else:
            plotSymbol = 'o-'

        figHandle#.set_size_inches(figureSize, forward=True)
        # plt.figure(figsize=figureSize)
        plt.clf()
        # print(strainsToPlot)
        colors = plt.get_cmap(self.colorMap)(np.linspace(0,1,len(strainsToPlot)))

        useNewColorScheme = 0
        if useNewColorScheme == 1:
            # Gather some information about the data
            uniques = dict()
            numUniques = dict()
            for identifier, col in zip(['experiment','strainID','identifier1','identifier2'],[0,1,2,3]):
                uniques[identifier] = set(row[col] for row in strainsToPlot)
                numUniques[identifier] = len(uniques[identifier])

            # Check number of unique identifier1s for each of the two identifier2s
            for identifier, col in zip(['experiment','strainID','identifier1','identifier2'],[0,1,2,3]):
                if identifier == 'identifier1':
                    uniques[identifier]

            # print(row[3] for row in strainsToPlot)
            lenEachUniqueID = []
            for id in uniques['identifier2']:
                lenEachUniqueID.append(len([0 for row in strainsToPlot if row[3] == id]))

            # Test coloring by
            cmap = []
            cmap.append('Blues')
            cmap.append('Greens')
            colors_test = []
            colors_test.append(plt.get_cmap(cmap[0])(np.linspace(0.2,0.9,lenEachUniqueID[0])))
            colors_test.append(plt.get_cmap(cmap[1])(np.linspace(0.2,0.9,lenEachUniqueID[1])))

            colorList = []
            i = 0
            j = 0
            for row in strainsToPlot:
                if row[3] == list(uniques['identifier2'])[0]:
                    colorList.append(colors_test[0][i])
                    i += 1
                if row[3] == list(uniques['identifier2'])[1]:
                    colorList.append(colors_test[1][j])
                    j += 1

            colors = colorList


        pltNum = 0
        handleArray = [None for i in range(len(strainsToPlot))]
        lineLabelsArray = [None for i in range(len(strainsToPlot))]
        for product in titersToPlot:
            pltNum += 1

            # Choose the subplot layout
            if len(titersToPlot) == 1:
                ax = plt.subplot(111)
            elif len(titersToPlot) < 5:
                ax = plt.subplot(1,len(titersToPlot),pltNum)
            elif len(titersToPlot) < 9:
                ax = plt.subplot(2,(len(titersToPlot)+1)/2,pltNum)
            else:
                raise Exception("Unimplemented Functionality")

            # Set some axis aesthetics
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            colorIndex = 0
            handle = dict()
            xlabel = 'Time (hours)'


            handle_ebar = []
            handle = []
            minOneLinePlotted = False

            for i, row in enumerate(strainsToPlot):
                replicateToPlot = row[5]
                if product in replicateToPlot.singleTrialList[0].products or (product == 'OD' and replicateToPlot.singleTrialList[0].OD != None):
                    # print(row)

                    lineLabelsArray[i] = (str(row[0])+'\t'+row[1]+'\t'+row[2]+'\t'+row[3]).expandtabs()
                    xData = replicateToPlot.t

                    if product == 'OD':
                        scaledTime = replicateToPlot.t
                        # Plot the fit curve
                        if plotCurveFit==True:
                            handleArray[i] = plt.plot(np.linspace(min(scaledTime),max(scaledTime),50),
                                                    replicateToPlot.avg.OD.returnCurveFitPoints(np.linspace(min(replicateToPlot.t),max(replicateToPlot.t),50)),
                                                   '-',lw=1.5,color=colors[colorIndex])[0]


                        # Plot the data
                        temp = plt.errorbar(scaledTime[::removePointFraction],
                                                   replicateToPlot.avg.OD.dataVec[::removePointFraction],
                                                   replicateToPlot.std.OD.dataVec[::removePointFraction],
                                                   lw=2.5,elinewidth=1,capsize=2,fmt=plotSymbol,markersize=5,color=colors[colorIndex])[0]
                        if plotCurveFit == False : handleArray[i] = temp

                        handleArray[i] = mpatches.Patch(color=colors[colorIndex])

                        # Fill in the error bar range
                        if shadeErrorRegion==True:
                            plt.fill_between(scaledTime,replicateToPlot.avg.OD.dataVec+replicateToPlot.std.OD.dataVec,
                                             replicateToPlot.avg.OD.dataVec-replicateToPlot.std.OD.dataVec,
                                             facecolor=colors[colorIndex],alpha=0.1)
                        # Add growth rates at end of curve
                        if showGrowthRates==True:
                            plt.text(scaledTime[-1]+0.5,
                                     replicateToPlot.avg.OD.returnCurveFitPoints(np.linspace(min(replicateToPlot.t),max(replicateToPlot.t),50))[-1],
                                     '$\mu$ = '+'{:.2f}'.format(replicateToPlot.avg.OD.rate[1]) + ' $\pm$ ' + '{:.2f}'.format(replicateToPlot.std.OD.rate[1])+', n='+str(len(replicateToPlot.replicateIDs)-len(replicateToPlot.badReplicates)),
                                     verticalalignment='center')
                        ylabel = 'OD$_{600}$'
                    else:

                        scaledTime = replicateToPlot.t

                        handleArray[i] = plt.plot(np.linspace(min(scaledTime),max(scaledTime),50),
                                                replicateToPlot.avg.products[product].returnCurveFitPoints(np.linspace(min(replicateToPlot.t),max(replicateToPlot.t),50)),
                                               '-',lw=0.5,color=colors[colorIndex])[0]
                        handleArray[i] = mpatches.Patch(color=colors[colorIndex])

                        handle_ebar.append(plt.errorbar(replicateToPlot.t,replicateToPlot.avg.products[product].dataVec,replicateToPlot.std.products[product].dataVec,lw=2.5,elinewidth=1,capsize=2,fmt='o-',color=colors[colorIndex]))
                        ylabel = product+" Titer (g/L)"
                    minOneLinePlotted = True
                colorIndex += 1
            if minOneLinePlotted == True:
                plt.xlabel(xlabel)
                plt.ylabel(ylabel)
                ymin, ymax = plt.ylim()
                xmin, xmax = plt.xlim()
                plt.xlim([0,xmax*1.2])
                plt.ylim([0,ymax])
        # plt.style.use('ggplot')
        plt.tight_layout()
        plt.tick_params(right="off",top="off")

        plt.legend(handleArray,lineLabelsArray,bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0, frameon=False)
        plt.subplots_adjust(right=0.7)

        if len(titersToPlot) == 1:
            plt.legend(handleArray,lineLabelsArray,bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0, frameon=False)
            plt.subplots_adjust(right=0.7)
        elif len(titersToPlot) < 4:
            plt.legend(handleArray,lineLabelsArray,bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0, frameon=False)
            plt.subplots_adjust(right=0.75)
        else:
            plt.legend(handleArray,lineLabelsArray,bbox_to_anchor=(1.05, 1.1), loc=6, borderaxespad=0, frameon=False)
            plt.subplots_adjust(right=0.75)

        # Save the figure
        # plt.savefig(os.path.join(os.path.dirname(__file__),'Figures/'+time.strftime('%y')+'.'+time.strftime('%m')+'.'+time.strftime('%d')+" H"+time.strftime('%H')+'-M'+time.strftime('%M')+'-S'+time.strftime('%S')+'.png'))
        # plt.show()

    def printGenericTimeCourse_plotly(self, dbName = '', strainsToPlot=[], titersToPlot=[], removePointFraction=1, shadeErrorRegion=False, showGrowthRates=True, plotCurveFit=False ):
        # Load plotly
        from plotly import tools
        from plotly.offline import plot
        import plotly.graph_objs as go

        # Load data into replciate experiment object
        conn = sql.connect(dbName)
        c = conn.cursor()
        replicateTrialList = []
        print('strains to plot',strainsToPlot)
        for strain in strainsToPlot:
            tempReplicateTrial = ReplicateTrial()
            tempReplicateTrial.loadFromDB(c = c, replicateID = strain)
            replicateTrialList.append(tempReplicateTrial)
            print('strainID: ',tempReplicateTrial.runIdentifier.strainID)
        conn.close()

        # Plot all product titers if none specified TODO: Add an option to plot OD as well
        if titersToPlot == []:
            raise Exception('No titers defined to plot')
            titersToPlot = ['OD']#self.getAllTiters()
        else:
            ... #TODO Refactor this for new DB struct
            # # Check if titer exists for each strainToPlot
            # titersToPlotPerStrain = []
            # for row in strainsToPlot:
            #     temp = []
            #     for i, product in enumerate(titersToPlot):
            #         if product in row[5].singleTrialList[0].products:
            #             temp.append(True)
            #         else:
            #             temp.append(False)
            #     titersToPlotPerStrain.append(temp)

        # titerNames = []
        # for experiment in self.experimentList:
        #     for key in experiment[2].replicateExperimentObjectDict:
        #         for singleExperiment in experiment[2].replicateExperimentObjectDict[key].singleTrialList:
        #             for product in singleExperiment.products:
        #                titerNames.append(product)
        #
        #             if singleExperiment.OD != None:
        #                 titerNames.append('OD')
        # uniqueTiterNames = set(titerNames)


        colors = plt.get_cmap(self.colorMap)(np.linspace(0,1,len(strainsToPlot)))

        # Choose the subplot layout
        if len(titersToPlot) == 1:
            rows = 1
            fig = tools.make_subplots(rows=1, cols=1)
        elif len(titersToPlot) < 5:
            rows = 1
            fig = tools.make_subplots(rows=1, cols=len(titersToPlot))
        elif len(titersToPlot) < 9:
            rows = 2
            fig = tools.make_subplots(rows=2, cols=4)
        else:
            raise Exception("Unimplemented Functionality")


        pltNum = 0

        for product in titersToPlot:
            pltNum += 1

            colorIndex = 0
            xlabel = 'Time (hours)'

            trace = []
            for replicate in replicateTrialList:
                xData = replicate.t
                if product == 'OD' or product == 'Ec_biomass_iJO1366_core_53p95M' or product == 'OD600':
                    scaledTime = replicate.t
                    # Plot the fit curve
                    print(replicate.avg.OD.dataVec[::removePointFraction], removePointFraction)
                    if plotCurveFit==True:
                        trace.append(go.Scatter(x=np.linspace(min(scaledTime),max(scaledTime),50),
                                                y=replicate.avg.OD.returnCurveFitPoints(np.linspace(min(replicate.t),max(replicate.t),50)),
                                                mode='line',
                                                name=replicate.runIdentifier.strainID+'\t'+replicate.runIdentifier.identifier1+'\t'+replicate.runIdentifier.identifier2,
                                                line = {'color': 'rgba('+str(list(colors[colorIndex])).replace('[',"").replace(']',"")+')'}
                                               ))


                    # Plot the data
                    # print(vars(replicate.avg.OD.runIdentifier))
                    trace = go.Scatter(x=scaledTime[::removePointFraction],
                                        y=replicate.avg.OD.dataVec[::removePointFraction],
                                        error_y = {
                                            'type': 'data',
                                            'array':replicate.std.OD.dataVec[::removePointFraction],
                                            'visible':True,
                                            'color':'rgba('+str(list(colors[colorIndex])).replace('[',"").replace(']',"")+')'},
                                        mode = 'markers',
                                        marker = {'color': 'rgba('+str(list(colors[colorIndex])).replace('[',"").replace(']',"")+')'},
                                        name=replicate.runIdentifier.strainID+replicate.runIdentifier.identifier1+replicate.runIdentifier.identifier2)

                    # # Fill in the error bar range
                    # if shadeErrorRegion==True:
                    #     plt.fill_between(scaledTime,self.replicateExperimentObjectDict[key].avg.OD.dataVec+self.replicateExperimentObjectDict[key].std.OD.dataVec,
                    #                      self.replicateExperimentObjectDict[key].avg.OD.dataVec-self.replicateExperimentObjectDict[key].std.OD.dataVec,
                    #                      facecolor=colors[colorIndex],alpha=0.1)
                    # # Add growth rates at end of curve
                    # if showGrowthRates==True:
                    #     plt.text(scaledTime[-1]+0.5,
                    #              self.replicateExperimentObjectDict[key].avg.OD.returnCurveFitPoints(np.linspace(min(self.replicateExperimentObjectDict[key].t),max(self.replicateExperimentObjectDict[key].t),50))[-1],
                    #              '$\mu$ = '+'{:.2f}'.format(self.replicateExperimentObjectDict[key].avg.OD.rate[1]) + ' $\pm$ ' + '{:.2f}'.format(self.replicateExperimentObjectDict[key].std.OD.rate[1])+', n='+str(len(self.replicateExperimentObjectDict[key].replicateIDs)-len(self.replicateExperimentObjectDict[key].badReplicates)),
                    #              verticalalignment='center')
                    # ylabel = 'OD$_{600}$'
                elif product == 'EX_glc_e':
                    # raise Exception('Unimplemented functionality for titers other than OD')
                    scaledTime = replicate.t
                    trace = go.Scatter(x=scaledTime[::removePointFraction],
                                        y=replicate.avg.substrate.dataVec[::removePointFraction],
                                        error_y = {
                                            'type': 'data',
                                            'array': replicate.std.substrate.dataVec[::removePointFraction],
                                            'visible':True,
                                            'color':'rgba('+str(list(colors[colorIndex])).replace('[',"").replace(']',"")+')'},
                                        mode = 'markers',
                                        marker = {'color': 'rgba('+str(list(colors[colorIndex])).replace('[',"").replace(']',"")+')'},
                                        showlegend = False)

                    # handle[key] = plt.plot(np.linspace(min(scaledTime),max(scaledTime),50),
                    #                         replicate.avg.products[product].returnCurveFitPoints(np.linspace(min(replicate.t),max(replicate.t),50)),
                    #                        '-',lw=0.5,color=colors[colorIndex])

                    ylabel = product+" Titer (g/L)"
                else:
                    # raise Exception('Unimplemented functionality for titers other than OD')
                    scaledTime = replicate.t
                    trace = go.Scatter(x=scaledTime[::removePointFraction],
                                        y=replicate.avg.products[product].dataVec[::removePointFraction],
                                        error_y = {
                                            'type': 'data',
                                            'array': replicate.std.products[product].dataVec[::removePointFraction],
                                            'visible':True,
                                            'color':'rgba('+str(list(colors[colorIndex])).replace('[',"").replace(']',"")+')'},
                                        mode = 'markers',
                                        marker = {'color': 'rgba('+str(list(colors[colorIndex])).replace('[',"").replace(']',"")+')'},
                                        showlegend = False)

                    # handle[key] = plt.plot(np.linspace(min(scaledTime),max(scaledTime),50),
                    #                         replicate.avg.products[product].returnCurveFitPoints(np.linspace(min(replicate.t),max(replicate.t),50)),
                    #                        '-',lw=0.5,color=colors[colorIndex])

                    ylabel = product+" Titer (g/L)"

                colorIndex += 1

                if pltNum > 4:
                    row = 2
                    col = pltNum-4
                else:
                    row = 1
                    col = pltNum
                print(row, col)
                fig.append_trace(trace, row, col)
            print('xaxis'+str(pltNum))
            fig['layout']['xaxis'+str(pltNum)].update(title='Time (hours)')
            fig['layout']['yaxis'+str(pltNum)].update(title=product+' Titer')
            fig['layout'].update(height= 800)

        # layout = go.Layout(
        #     xaxis=dict(
        #         title='Time (hours)'
        #     ),
        #     yaxis=dict(
        #         title='OD600'
        #     ),
        #     height = 600
        # )
        # fig.update(layout)
        # fig['layout'].update = go.Figure(data=trace, layout=layout)
        return plot(fig, show_link=False, output_type='div')

class Experiment(object):
    colorMap = 'Set2'

    def __init__(self, info = None):
        # Initialize variables
        self.timePointList = []#dict()
        self.titerObjectDict = dict()
        self.singleExperimentObjectDict = dict()
        self.replicateExperimentObjectDict = dict()
        self.infoKeys = ['importDate','runStartDate','runEndDate','experimentTitle','principalScientistName','secondaryScientistName','mediumBase','mediumSupplements','notes']
        if info != None:    self.info = {key:info[key] for key in self.infoKeys if key in info}
        else:   info = dict()

        # # SQLite stuff
        # # Initialize database
        # conn = sql.connect('temptSQLite3db.db')
        # c = conn.cursor()
        # # for table in ['timePointTable','timeCourseTable','singleExperimentTable','replicateExperimentTable']:
        # #     c.execute("CREATE TABLE IF NOT EXISTS %s (datestamp TEXT, strainID TEXT, identifier1 TEXT, identifier2 TEXT, replicate INTEGER, time REAL, titerName TEXT, titerType TEXT, timeVec BLOB, dataVec BLOB) "%table)
        #
        # c.execute("""\
        #    CREATE TABLE IF NOT EXISTS TimeCourseTable
        #    (importDate TEXT, runStartDate TEXT, runEndDate TEXT, principalScientistName TEXT,
        #    secondaryScientistName TEXT, mediumBase TEXT, mediumSupplements TEXT, notes TEXT,
        #    strainID TEXT, identifier1 TEXT, identifier2 TEXT, identifier3 TEXT, replicate INTEGER,
        #    titerType TEXT, titerName TEXT, titerID TEXT, timeVec BLOB, dataVec BLOB)
        # """)
        #
        # conn.commit()
        # c.close()
        # conn.close()

    def readFromDB(self, dbName):
        pass

    def commitToDB(self, dbName):
        conn = sql.connect(dbName)
        c = conn.cursor()
        preppedCols = list(self.info.keys())
        preppedColQuery = ', '.join(col for col in preppedCols)
        preppedColData = [self.info[key] for key in preppedCols]
        c.execute("""\
           INSERT INTO experimentTable
           ("""+preppedColQuery+""") VALUES ("""+', '.join('?' for a in preppedColData)+""")""",preppedColData)
        c.execute("""SELECT MAX(experimentID) FROM experimentTable""")
        experimentID = c.fetchall()[0][0]
        for key in self.replicateExperimentObjectDict:
            self.replicateExperimentObjectDict[key].commitToDB(experimentID, c = c)


        conn.commit()
        c.close()

        print('Committed experiment #',experimentID,' to DB ',dbName)
        return experimentID

    def loadFromDB(self, dbName, experimentID):
        conn = sql.connect(dbName)
        c = conn.cursor()
        c.execute("""SELECT * FROM experimentTable WHERE (experimentID == ?)""",(experimentID,))
        self.exptDescription = {key: data for data, key in zip(c.fetchall()[0],[elem[0] for elem in c.description])}

        # Build the replicate experiment objects
        c.execute("""SELECT  strainID, identifier1, identifier2, identifier3, replicateID FROM replicateTable
                WHERE experimentID == ?""",(experimentID,))
        for row in c.fetchall():
            self.replicateExperimentObjectDict[row[0]+row[1]+row[2]] = ReplicateTrial()
            self.replicateExperimentObjectDict[row[0]+row[1]+row[2]].runIdentifier.strainID = row[0]
            self.replicateExperimentObjectDict[row[0]+row[1]+row[2]].runIdentifier.identifier1 = row[1]
            self.replicateExperimentObjectDict[row[0]+row[1]+row[2]].runIdentifier.identifier2 = row[2]
            self.replicateExperimentObjectDict[row[0]+row[1]+row[2]].runIdentifier.identifier3 = row[3]
            self.replicateExperimentObjectDict[row[0]+row[1]+row[2]].loadFromDB(c = c, replicateID = row[4])

        a = 2

    def getAllStrains_django(self, dbName, experimentID):
        """
        :param dbName:
        :param experimentID:
        :return:
        """
        conn = sql.connect(dbName)
        c = conn.cursor()
        c.execute("""SELECT * FROM experimentTable WHERE (experimentID == ?)""",(experimentID,))
        exptDescription = {key: data for data, key in zip(c.fetchall()[0],[elem[0] for elem in c.description])}

        # Build the replicate experiment objects
        c.execute("""SELECT  strainID, identifier1, identifier2, identifier3, replicateID, experimentID FROM replicateTable
                WHERE experimentID == ? ORDER BY strainID DESC, identifier1 DESC, identifier2 DESC""",(experimentID,))
        strainDescriptions = []
        for row in c.fetchall():
            strainDescriptions.append({key: data for data, key in zip(row,[elem[0] for elem in c.description])})
        c.close()
        return strainDescriptions

    def plottingGUI(self):
        app = QtGui.QApplication(sys.argv)

        main = Window(self)
        main.showMaximized()

        sys.exit(app.exec_())

    def getAllStrains(self):
        temp = [key for key in self.replicateExperimentObjectDict if self.replicateExperimentObjectDict[key].runIdentifier.identifier1 != '']
        temp.sort()
        return temp



    def getAllTiters(self):
        titersToPlot = [[[product for product in singleExperiment.products] for singleExperiment in self.replicateExperimentObjectDict[key].singleTrialList] for key in self.replicateExperimentObjectDict]

        # Flatten list and find the uniques
        titersToPlot = [y for x in titersToPlot for y in x]
        titersToPlot =  list(set([y for x in titersToPlot for y in x]))

        ODList = [[singleExperiment.OD for singleExperiment in self.replicateExperimentObjectDict[key].singleTrialList] for key in self.replicateExperimentObjectDict]
        ODList = list(set([y for x in ODList for y in x]))

        # print(ODList)
        if ODList[0] != None:
            titersToPlot.append('OD')

        return titersToPlot

    def getTimeCourseData(self, strainName, titerName, replicate):
        pass

    def parseRawData(self, dataFormat, fileName = None, data = None ):
        print('STARTED PARSING DATA:')

        t0 = time.time()
        if data == None:
            if fileName == None:
                raise Exception('No data or file name given to load data from')
            # Get data from xlsx file
            data = get_data(fileName)
            print('Imported data from %s' % (fileName))

        if dataFormat == 'NV_OD':
            t0 = time.time()
            if fileName:
                # Check for correct data for import
                if 'OD' not in data.keys():
                    raise Exception("No sheet named 'OD' found")
                else:
                    ODDataSheetName = 'OD'

                data = data[ODDataSheetName]

            # Parse data into timeCourseObjects
            skippedLines = 0
            timeCourseObjectList = dict()
            for row in data[1:]:
                temp_run_identifier_object = RunIdentifier()
                if type("asdf") == type(row[0]):
                    temp_run_identifier_object.getRunIdentifier(row[0])
                    temp_run_identifier_object.titerName = 'OD600'
                    temp_run_identifier_object.titerType = 'OD'
                    tempTimeCourseObject = TimeCourse()
                    tempTimeCourseObject.runIdentifier = temp_run_identifier_object
                    # Data in seconds, data required to be in hours
                    # print(data[0][1:])
                    tempTimeCourseObject.timeVec = np.array(np.divide(data[0][1:], 3600))

                    tempTimeCourseObject.dataVec = np.array(row[1:])
                    self.titerObjectDict[tempTimeCourseObject.getTimeCourseID()] = copy.copy(tempTimeCourseObject)

                    # if tempTimeCourseObject.getTimeCourseID() in timeCourseObjectList:
                    #     print('Duplicate Object Found')
                    #     #raise Exception("Duplicate time course name found")
                    # else:
            tf = time.time()
            print("Parsed %i timeCourseObjects in %0.3fs\n" % (len(self.titerObjectDict),tf-t0))
            self.parseTiterObjectCollection(self.titerObjectDict)

        if dataFormat == 'NV_titers':
            substrateName = 'Glucose'
            titerDataSheetName = "titers"

            if 'titers' not in data.keys():
                raise Exception("No sheet named 'titers' found")

            ######## Initialize variables
            titerNameColumn = dict()
            for i in range(1,len(data[titerDataSheetName][2])):
                titerNameColumn[data[titerDataSheetName][2][i]] = i

            tempTimePointCollection = dict()
            for names in titerNameColumn:
                tempTimePointCollection[names] = []

            timePointCollection = []
            skippedLines = 0
            # timePointList = []

            ######## Parse the titer data into single experiment object list
            ### NOTE: THIS PARSER IS NOT GENERIC AND MUST BE MODIFIED FOR YOUR SPECIFIC INPUT TYPE ###
            for i in range(4, len(data['titers'])):
                if type("asdf") == type(data['titers'][i][0]):  #Check if the data is a string
                    tempParsedIdentifier = data['titers'][i][0].split(',')  #Parse the string using comma delimiter
                    if len(tempParsedIdentifier) >= 3:  #Ensure corect number of identifiers TODO make this general
                        tempRunIdentifierObject = RunIdentifier()
                        tempParsedStrainIdentifier = tempParsedIdentifier[0].split("+")
                        tempRunIdentifierObject.strainID = tempParsedStrainIdentifier[0]
                        tempRunIdentifierObject.identifier1 = tempParsedStrainIdentifier[1]
                        # tempRunIdentifierObject.identifier2 = tempParsedIdentifier[2]
                        tempParsedReplicate = tempParsedIdentifier[1].split('=')
                        tempRunIdentifierObject.replicate = int(tempParsedReplicate[1])#tempParsedIdentifier[1]
                        tempParsedTime = tempParsedIdentifier[2].split('=')
                        tempRunIdentifierObject.t = float(tempParsedTime[1])#tempParsedIdentifier[2]

                        for key in tempTimePointCollection:
                            tempRunIdentifierObject.titerName = key
                            if key == 'Glucose':
                                tempRunIdentifierObject.titerType = 'substrate'
                            else:
                                tempRunIdentifierObject.titerType = 'product'
                            self.timePointList.append(TimePoint(copy.copy(tempRunIdentifierObject), key, tempRunIdentifierObject.t, data['titers'][i][titerNameColumn[key]]))

                    else:
                        skippedLines += 1
                else:
                    skippedLines += 1

        if dataFormat == 'NV_titers0.2':
            substrateName = 'Glucose'
            titerDataSheetName = "titers"

            if 'titers' not in data.keys():
                raise Exception("No sheet named 'titers' found")

            ######## Initialize variables
            titerNameColumn = dict()
            for i in range(1,len(data[titerDataSheetName][2])):
                titerNameColumn[data[titerDataSheetName][2][i]] = i

            tempTimePointCollection = dict()
            for names in titerNameColumn:
                tempTimePointCollection[names] = []

            timePointCollection = []
            skippedLines = 0
            # timePointList = []

            ######## Parse the titer data into single experiment object list
            ### NOTE: THIS PARSER IS NOT GENERIC AND MUST BE MODIFIED FOR YOUR SPECIFIC INPUT TYPE ###
            for i in range(4, len(data['titers'])):
                if type("asdf") == type(data['titers'][i][0]):  #Check if the data is a string
                    temp_run_identifier_object = RunIdentifier()
                    temp_run_identifier_object.getRunIdentifier(data['titers'][i][0])

                    tempParsedIdentifier = data['titers'][i][0].split(',')  #Parse the string using comma delimiter

                    temp_run_identifier_object.t = 15.#tempParsedIdentifier[2]

                    for key in tempTimePointCollection:
                        temp_run_identifier_object.titerName = key
                        if key == 'Glucose':
                            temp_run_identifier_object.titerType = 'substrate'
                            self.timePointList.append(TimePoint(copy.copy(temp_run_identifier_object), key, 0, 12))
                        else:
                            temp_run_identifier_object.titerType = 'product'
                            self.timePointList.append(TimePoint(copy.copy(temp_run_identifier_object), key, 0, 0))
                        self.timePointList.append(TimePoint(copy.copy(temp_run_identifier_object), key, temp_run_identifier_object.t, data['titers'][i][titerNameColumn[key]]))


                    else:
                        skippedLines += 1
                else:
                    skippedLines += 1

            tf = time.time()
            print("Parsed %i timeCourseObjects in %0.3fs\n" % (len(self.timePointList),tf-t0))
            print("Number of lines skipped: ",skippedLines)
            self.parseTimePointCollection(self.timePointList)


    # def parseTimePointCollection(self, timePointList):  # Combine all time points into time vectors for experiments
    # def parseTiterObjectCollection(self, titerObjectDict):  # Combine all the titer objects into single experiments
    #                                                         # (e.g. all titers for one strain)
    # def parseSingleExperimentObjectList(self, singleExperimentObjectList):  # Parse replicate experiments


    def parseTimePointCollection(self, timePointList):
        print('Parsing time point list...')
        t0 = time.time()
        for timePoint in timePointList:
            flag = 0
            if timePoint.getUniqueTimePointID() in self.titerObjectDict:
                self.titerObjectDict[timePoint.getUniqueTimePointID()].addTimePoint(timePoint)
            else:
                self.titerObjectDict[timePoint.getUniqueTimePointID()] = TimeCourse()
                self.titerObjectDict[timePoint.getUniqueTimePointID()].addTimePoint(timePoint)
        tf = time.time()
        print("Parsed %i titer objects in %0.1fs\n" % (len(self.titerObjectDict),(tf-t0)))
        self.parseTiterObjectCollection(self.titerObjectDict)

    def parseTiterObjectCollection(self, titerObjectDict):
        print('Parsing titer object list...')
        t0 = time.time()
        for titerObjectDictKey in titerObjectDict:
            if titerObjectDict[titerObjectDictKey].getTimeCourseID() in self.singleExperimentObjectDict:
                self.singleExperimentObjectDict[titerObjectDict[titerObjectDictKey].getTimeCourseID()].addTiterObject(titerObjectDict[titerObjectDictKey])
            else:
                self.singleExperimentObjectDict[titerObjectDict[titerObjectDictKey].getTimeCourseID()] = SingleTrial()
                self.singleExperimentObjectDict[titerObjectDict[titerObjectDictKey].getTimeCourseID()].addTiterObject(titerObjectDict[titerObjectDictKey])
        tf = time.time()
        print("Parsed %i titer objects in %0.1fms\n" % (len(self.singleExperimentObjectDict),(tf-t0)*1000))
        self.parseSingleExperimentObjectList(self.singleExperimentObjectDict)

    def parseSingleExperimentObjectList(self, singleExperimentObjectList):
        print('Parsing single experiment object list...')
        t0 = time.time()
        for key in singleExperimentObjectList:
            flag = 0
            for key2 in self.replicateExperimentObjectDict:
                if key2 == singleExperimentObjectList[key].getUniqueReplicateID():
                    self.replicateExperimentObjectDict[key2].addReplicateExperiment(singleExperimentObjectList[key])
                    flag = 1
                    break
            if flag == 0:
                self.replicateExperimentObjectDict[singleExperimentObjectList[key].getUniqueReplicateID()] = ReplicateTrial()
                self.replicateExperimentObjectDict[singleExperimentObjectList[key].getUniqueReplicateID()].addReplicateExperiment(singleExperimentObjectList[key])
        tf = time.time()
        print("Parsed %i titer objects in %0.1fs\n" % (len(self.replicateExperimentObjectDict),(tf-t0)))

    def addReplicateTrial(self, replicateTrial):
        self.replicateExperimentObjectDict[replicateTrial.singleTrialList[0].getUniqueReplicateID()] = replicateTrial

    def pickle(self, fileName):
        pickle.dump([self.timePointList, self.titerObjectDict, self.singleExperimentObjectDict, self.replicateExperimentObjectDict], open(fileName,'wb'))

    def unpickle(self, fileName):
        t0 = time.time()
        with open(fileName,'rb') as data:
            self.timePointList, self.titerObjectDict, self.singleExperimentObjectDict, self.replicateExperimentObjectDict = pickle.load(data)
        print('Read data from %s in %0.3fs' % (fileName,time.time()-t0))

    def printGenericTimeCourse(self, figHandle = [], strainsToPlot=[], titersToPlot=[], removePointFraction=1, shadeErrorRegion=False, showGrowthRates=True, plotCurveFit=True ):
        if figHandle == []:
            figHandle = plt.figure(figsize=(12,8))

        figHandle.set_facecolor('w')

        if strainsToPlot == []:
            strainsToPlot = self.getAllStrains()
        # Plot all product titers if none specified TODO: Add an option to plot OD as well
        if titersToPlot == []:
            titersToPlot = self.getAllTiters()

        # Determine optimal figure size
        if len(titersToPlot) == 1:
            figureSize = (12,6)
        if len(titersToPlot) > 1:
            figureSize = (12,3.5)
        if len(titersToPlot) > 4:
            figureSize = (12,7)

        if plotCurveFit==True:
            plotSymbol = 'o'
        else:
            plotSymbol = 'o-'

        figHandle#.set_size_inches(figureSize, forward=True)
        # plt.figure(figsize=figureSize)
        plt.clf()

        colors = plt.get_cmap(self.colorMap)(np.linspace(0,1,len(strainsToPlot)))

        pltNum = 0
        for product in titersToPlot:
            pltNum += 1

            # Choose the subplot layout
            if len(titersToPlot) == 1:
                ax = plt.subplot(111)
            elif len(titersToPlot) < 5:
                ax = plt.subplot(1,len(titersToPlot),pltNum)
            elif len(titersToPlot) < 9:
                ax = plt.subplot(2,(len(titersToPlot)+1)/2,pltNum)
            else:
                raise Exception("Unimplemented Functionality")

            # Set some axis aesthetics
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            colorIndex = 0
            handle = dict()
            xlabel = 'Time (hours)'
            for key in strainsToPlot:
                xData = self.replicateExperimentObjectDict[key].t
                if product == 'OD':
                    scaledTime = self.replicateExperimentObjectDict[key].t
                    # Plot the fit curve
                    if plotCurveFit==True:
                        handle[key] = plt.plot(np.linspace(min(scaledTime),max(scaledTime),50),
                                                self.replicateExperimentObjectDict[key].avg.OD.returnCurveFitPoints(np.linspace(min(self.replicateExperimentObjectDict[key].t),max(self.replicateExperimentObjectDict[key].t),50)),
                                               '-',lw=1.5,color=colors[colorIndex])
                    # Plot the data
                    handle[key] = plt.errorbar(scaledTime[::removePointFraction],
                                               self.replicateExperimentObjectDict[key].avg.OD.dataVec[::removePointFraction],
                                               self.replicateExperimentObjectDict[key].std.OD.dataVec[::removePointFraction],
                                               lw=2.5,elinewidth=1,capsize=2,fmt=plotSymbol,markersize=5,color=colors[colorIndex])
                    # Fill in the error bar range
                    if shadeErrorRegion==True:
                        plt.fill_between(scaledTime,self.replicateExperimentObjectDict[key].avg.OD.dataVec+self.replicateExperimentObjectDict[key].std.OD.dataVec,
                                         self.replicateExperimentObjectDict[key].avg.OD.dataVec-self.replicateExperimentObjectDict[key].std.OD.dataVec,
                                         facecolor=colors[colorIndex],alpha=0.1)
                    # Add growth rates at end of curve
                    if showGrowthRates==True:
                        plt.text(scaledTime[-1]+0.5,
                                 self.replicateExperimentObjectDict[key].avg.OD.returnCurveFitPoints(np.linspace(min(self.replicateExperimentObjectDict[key].t),max(self.replicateExperimentObjectDict[key].t),50))[-1],
                                 '$\mu$ = '+'{:.2f}'.format(self.replicateExperimentObjectDict[key].avg.OD.rate[1]) + ' $\pm$ ' + '{:.2f}'.format(self.replicateExperimentObjectDict[key].std.OD.rate[1])+', n='+str(len(self.replicateExperimentObjectDict[key].replicateIDs)-len(self.replicateExperimentObjectDict[key].badReplicates)),
                                 verticalalignment='center')
                    ylabel = 'OD$_{600}$'
                else:
                    scaledTime = self.replicateExperimentObjectDict[key].t

                    # handle[key] = plt.plot(np.linspace(min(scaledTime),max(scaledTime),50),
                    #                         self.replicateExperimentObjectDict[key].avg.products[product].returnCurveFitPoints(np.linspace(min(self.replicateExperimentObjectDict[key].t),max(self.replicateExperimentObjectDict[key].t),50)),
                    #                        '-',lw=0.5,color=colors[colorIndex])
                    print(key)
                    print(product)
                    print(self.replicateExperimentObjectDict[key].avg.products.keys())
                    handle[key] = plt.errorbar(self.replicateExperimentObjectDict[key].t[::removePointFraction],self.replicateExperimentObjectDict[key].avg.products[product].dataVec[::removePointFraction],self.replicateExperimentObjectDict[key].std.products[product].dataVec[::removePointFraction],lw=2.5,elinewidth=1,capsize=2,fmt='o-',color=colors[colorIndex])
                    ylabel = product+" Titer (g/L)"

                colorIndex += 1
                # plt.show()
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            ymin, ymax = plt.ylim()
            xmin, xmax = plt.xlim()
            plt.xlim([0,xmax*1.2])
            plt.ylim([0,ymax])
        # plt.style.use('ggplot')
        plt.tight_layout()
        plt.tick_params(right="off",top="off")
        # plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0, frameon=False)
        plt.subplots_adjust(right=0.7)

        if len(titersToPlot) == 1:
            plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0, frameon=False)
            plt.subplots_adjust(right=0.7)
        elif len(titersToPlot) < 5:
            plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0, frameon=False)
            plt.subplots_adjust(right=0.75)
        else:
            plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.05, 1.1), loc=6, borderaxespad=0, frameon=False)
            plt.subplots_adjust(right=0.75)

        # Save the figure
        # plt.savefig(os.path.join(os.path.dirname(__file__),'Figures/'+time.strftime('%y')+'.'+time.strftime('%m')+'.'+time.strftime('%d')+" H"+time.strftime('%H')+'-M'+time.strftime('%M')+'-S'+time.strftime('%S')+'.png'))
        # plt.show()

    def printGenericTimeCourse_plotly(self, figHandle = [], strainsToPlot=[], titersToPlot=[], removePointFraction=4, shadeErrorRegion=False, showGrowthRates=False, plotCurveFit=True ):
        from plotly import tools
        from plotly.offline import iplot, plot
        from plotly.graph_objs import Scatter
        import plotly.graph_objs as go

        if strainsToPlot == []:
            strainsToPlot = self.getAllStrains()

        # Plot all product titers if none specified TODO: Add an option to plot OD as well
        if titersToPlot == []:
            titersToPlot = self.getAllTiters()


        # Determine optimal figure size
        if len(titersToPlot) == 1:
            figureSize = (12,6)
        if len(titersToPlot) > 1:
            figureSize = (12,3.5)
        if len(titersToPlot) > 4:
            figureSize = (12,7)

        if plotCurveFit==True:
            plotSymbol = 'o'
        else:
            plotSymbol = 'o-'


        colors = plt.get_cmap(self.colorMap)(np.linspace(0,1,len(strainsToPlot)))





        pltNum = 0
        for product in titersToPlot:
            pltNum += 1

            # Choose the subplot layout
            if len(titersToPlot) == 1:
                ax = plt.subplot(111)
            elif len(titersToPlot) < 5:
                ax = plt.subplot(1,len(titersToPlot),pltNum)
            elif len(titersToPlot) < 9:
                ax = plt.subplot(2,(len(titersToPlot)+1)/2,pltNum)
            else:
                raise Exception("Unimplemented Functionality")


            colorIndex = 0
            handle = dict()
            xlabel = 'Time (hours)'
            trace = []
            for key in strainsToPlot:
                xData = self.replicateExperimentObjectDict[key].t
                if product == 'OD':
                    scaledTime = self.replicateExperimentObjectDict[key].t
                    # Plot the fit curve
                    if plotCurveFit==True:
                        trace.append(Scatter(x=np.linspace(min(scaledTime),max(scaledTime),50),
                                                y=self.replicateExperimentObjectDict[key].avg.OD.returnCurveFitPoints(np.linspace(min(self.replicateExperimentObjectDict[key].t),max(self.replicateExperimentObjectDict[key].t),50)),
                                                mode='line',
                                                name=key,
                                                line = {'color': 'rgba('+str(list(colors[colorIndex])).replace('[',"").replace(']',"")+')'}
                                               ))


                    # Plot the data
                    trace.append(Scatter(x=scaledTime[::removePointFraction],
                                        y=self.replicateExperimentObjectDict[key].avg.OD.dataVec[::removePointFraction],
                                        error_y = {
                                            'type': 'data',
                                            'array':self.replicateExperimentObjectDict[key].std.OD.dataVec[::removePointFraction],
                                            'visible':True,
                                            'color':'rgba('+str(list(colors[colorIndex])).replace('[',"").replace(']',"")+')'},
                                        mode = 'markers',
                                        marker = {'color': 'rgba('+str(list(colors[colorIndex])).replace('[',"").replace(']',"")+')'},
                                        showlegend = False))

                    # Fill in the error bar range
                    if shadeErrorRegion==True:
                        plt.fill_between(scaledTime,self.replicateExperimentObjectDict[key].avg.OD.dataVec+self.replicateExperimentObjectDict[key].std.OD.dataVec,
                                         self.replicateExperimentObjectDict[key].avg.OD.dataVec-self.replicateExperimentObjectDict[key].std.OD.dataVec,
                                         facecolor=colors[colorIndex],alpha=0.1)
                    # Add growth rates at end of curve
                    if showGrowthRates==True:
                        plt.text(scaledTime[-1]+0.5,
                                 self.replicateExperimentObjectDict[key].avg.OD.returnCurveFitPoints(np.linspace(min(self.replicateExperimentObjectDict[key].t),max(self.replicateExperimentObjectDict[key].t),50))[-1],
                                 '$\mu$ = '+'{:.2f}'.format(self.replicateExperimentObjectDict[key].avg.OD.rate[1]) + ' $\pm$ ' + '{:.2f}'.format(self.replicateExperimentObjectDict[key].std.OD.rate[1])+', n='+str(len(self.replicateExperimentObjectDict[key].replicateIDs)-len(self.replicateExperimentObjectDict[key].badReplicates)),
                                 verticalalignment='center')
                    ylabel = 'OD$_{600}$'
                else:
                    scaledTime = self.replicateExperimentObjectDict[key].t

                    handle[key] = plt.plot(np.linspace(min(scaledTime),max(scaledTime),50),
                                            self.replicateExperimentObjectDict[key].avg.products[product].returnCurveFitPoints(np.linspace(min(self.replicateExperimentObjectDict[key].t),max(self.replicateExperimentObjectDict[key].t),50)),
                                           '-',lw=0.5,color=colors[colorIndex])

                    handle[key] = plt.errorbar(self.replicateExperimentObjectDict[key].t,self.replicateExperimentObjectDict[key].avg.products[product].dataVec,self.replicateExperimentObjectDict[key].std.products[product].dataVec,lw=2.5,elinewidth=1,capsize=2,fmt='o-',color=colors[colorIndex])
                    ylabel = product+" Titer (g/L)"

                colorIndex += 1

            # ymin, ymax = plt.ylim()
            # xmin, xmax = plt.xlim()
            # plt.xlim([0,xmax*1.2])
            # plt.ylim([0,ymax])
        layout = go.Layout(
            xaxis=dict(
                title='Time (hours)'
            ),
            yaxis=dict(
                title='OD600'
            ),
            height = 800,
            width = 1400,
            autosize = True
        )
        fig = go.Figure(data=trace, layout=layout)
        return plot(fig, show_link=False, output_type='div')

        # if len(titersToPlot) == 1:
        #     plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0, frameon=False)
        #     plt.subplots_adjust(right=0.7)
        # elif len(titersToPlot) < 5:
        #     plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0, frameon=False)
        #     plt.subplots_adjust(right=0.75)
        # else:
        #     plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.05, 1.1), loc=6, borderaxespad=0, frameon=False)
        #     plt.subplots_adjust(right=0.75)

        # Save the figure
        # plt.savefig(os.path.join(os.path.dirname(__file__),'Figures/'+time.strftime('%y')+'.'+time.strftime('%m')+'.'+time.strftime('%d')+" H"+time.strftime('%H')+'-M'+time.strftime('%M')+'-S'+time.strftime('%S')+'.png'))
        # plt.show()

    def printGrowthRateBarChart(self, figHandle=[], strainsToPlot=[], sortBy='identifier1'):
        if figHandle == []:
            figHandle = plt.figure(figsize=(9,5))

        if strainsToPlot == []:
            strainsToPlot = [key for key in self.replicateExperimentObjectDict]

        # Sort the strains to plot to HELP ensure that things are in the same order
        # TODO should find a better way to ensure this is the case
        strainsToPlot.sort()

        # Clear the plot and set some aesthetics
        plt.cla()
        ax = plt.subplot(111)
        figHandle.set_facecolor('w')
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Find all the unique identifier based on which identifier to 'sortBy'
        uniques = list(set([getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) for key in strainsToPlot]))
        uniques.sort()

        # Find max number of samples (in case they all aren't the same)
        maxSamples = 0
        for unique in uniques:
            if len([self.replicateExperimentObjectDict[key].avg.OD.rate[1] for key in strainsToPlot if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == unique]) > maxSamples:
                maxSamples = len([self.replicateExperimentObjectDict[key].avg.OD.rate[1] for key in strainsToPlot if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == unique])
                maxIndex = unique


        barWidth = 0.9/len(uniques)
        index = np.arange(maxSamples)
        colors = plt.get_cmap('Set2')(np.linspace(0,1.0,len(uniques)))

        i = 0
        handle = dict()
        for unique in uniques:
            handle[unique] = plt.bar(index[0:len([self.replicateExperimentObjectDict[key].avg.OD.rate[1] for key in strainsToPlot if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == unique])],
                    [self.replicateExperimentObjectDict[key].avg.OD.rate[1] for key in strainsToPlot if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == unique],
                    barWidth, yerr=[self.replicateExperimentObjectDict[key].std.OD.rate[1] for key in strainsToPlot if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == unique],
                    color = colors[i],ecolor='k',capsize=5,error_kw=dict(elinewidth=1, capthick=1))
            i += 1
            index = index+barWidth

        ax.yaxis.set_ticks_position('left')
        ax.xaxis.set_ticks_position('bottom')
        plt.ylabel('Growth Rate ($\mu$, h$^{-1}$)')
        xticklabel = ''
        for attribute in ['strainID','identifier1','identifier2']:
            if attribute != sortBy:
                xticklabel = xticklabel+attribute

        if 'strainID' == sortBy:
            tempticks =[self.replicateExperimentObjectDict[key].runIdentifier.identifier1+'+'+
                        self.replicateExperimentObjectDict[key].runIdentifier.identifier2 for key in strainsToPlot
                        if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == maxIndex]
        if 'identifier1' == sortBy:
            tempticks = [self.replicateExperimentObjectDict[key].runIdentifier.strainID +'+'+
                         self.replicateExperimentObjectDict[key].runIdentifier.identifier2 for key in strainsToPlot
                         if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == maxIndex]
        if 'identifier2' == sortBy:
            tempticks = [self.replicateExperimentObjectDict[key].runIdentifier.strainID +'+'+
                         self.replicateExperimentObjectDict[key].runIdentifier.identifier1 for key in strainsToPlot
                         if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == maxIndex]
        tempticks.sort()

        plt.xticks(index-0.4, tempticks, rotation='45', ha='right', va='top')
        plt.tight_layout()
        plt.subplots_adjust(right=0.75)
        #print([handle[key][0][0] for key in handle])
        plt.legend([handle[key][0] for key in uniques],uniques,bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0)
        # ax.hold(False)

        return figHandle

    def printEndPointYield(self, figHandle=[], strainsToPlot=[], titersToPlot=[], sortBy='identifier2', withLegend=2):

        if figHandle == []:
            figHandle = plt.figure(figsize=(9, 5))

        if strainsToPlot == []:
            strainsToPlot = self.getAllStrains()

        if titersToPlot == []:
            titersToPlot = self.getAllTiters()

        # Clear the plot and set some aesthetics
        plt.cla()
        ax = plt.subplot(111)
        figHandle.set_facecolor('w')
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # uniques = list(set([getattr(self.replicateExperimentObjectDict[key].RunIdentifier,sortBy) for key in strainsToPlot]))
        # uniques.sort()
        #
        # # Find max number of samples (in case they all aren't the same)
        # maxSamples = 0
        # for unique in uniques:
        #     if len([self.replicateExperimentObjectDict[key].avg.OD.rate[1] for key in strainsToPlot if getattr(self.replicateExperimentObjectDict[key].RunIdentifier,sortBy) == unique]) > maxSamples:
        #         maxSamples = len([self.replicateExperimentObjectDict[key].avg.OD.rate[1] for key in strainsToPlot if getattr(self.replicateExperimentObjectDict[key].RunIdentifier,sortBy) == unique])
        #         maxIndex = unique

        replicateExperimentObjectList = self.replicateExperimentObjectDict
        handle = dict()
        colors = plt.get_cmap('Set2')(np.linspace(0,1.0,len(strainsToPlot)))

        barWidth = 0.6
        pltNum = 0

        if withLegend == 2:
            # # First determine which items to separate plot by (titer/OD, strain, id1, id2)
            # # TODO implement this
            #
            # # Then determine which items to group the plot by



            for product in titersToPlot:
                uniques = list(set([getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) for key in strainsToPlot]))
                uniques.sort()

                # Find max number of samples (in case they all aren't the same)
                maxSamples = 0
                for unique in uniques:
                    if len([self.replicateExperimentObjectDict[key].avg.products[product] for key in strainsToPlot if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == unique]) > maxSamples:
                    # if len([self.replicateExperimentObjectDict[key].avg.products[prodKey] for prodkey in self.replicateExperimentObjectDict[key] for key in strainsToPlot if getattr(self.replicateExperimentObjectDict[key].RunIdentifier,sortBy) == unique]) > maxSamples:
                        maxSamples = len([self.replicateExperimentObjectDict[key].avg.products[product] for key in strainsToPlot if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == unique])
                        maxIndex = unique

                # Create empty arrays to store data
                endPointTiterAvg=[]
                endPointTiterStd=[]
                endPointTiterLabel=[]

                # Choose plot number
                pltNum += 1
                ax = plt.subplot(1,len(titersToPlot),pltNum)

                # Initial variables and choose plotting locations of bars
                location = 0

                # Prepare data for plotting
                for key in strainsToPlot:
                    if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == unique:
                        endPointTiterLabel.append(key)
                        endPointTiterAvg.append(replicateExperimentObjectList[key].avg.yields[product][-1])
                        endPointTiterStd.append(replicateExperimentObjectList[key].std.yields[product][-1])

                barWidth = 0.9/len(uniques)
                index = np.arange(maxSamples)
                colors = plt.get_cmap('Set2')(np.linspace(0,1.0,len(uniques)))

                i=0
                for unique in uniques:
                    print([self.replicateExperimentObjectDict[key].avg.yields[product][-1] for key in strainsToPlot if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == unique])
                    print(len([self.replicateExperimentObjectDict[key].avg.yields[product][-1] for key in strainsToPlot if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == unique]))
                    print([getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) for key in strainsToPlot if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == unique])
                    print()
                    handle[unique] = plt.bar(index[0:len([self.replicateExperimentObjectDict[key].avg.products[product] for key in strainsToPlot if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == unique])],
                                            [self.replicateExperimentObjectDict[key].avg.yields[product][-1] for key in strainsToPlot if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == unique],
                                            barWidth,
                                            yerr=[self.replicateExperimentObjectDict[key].std.yields[product][-1] for key in strainsToPlot if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == unique],
                                            color = colors[i],ecolor='k',capsize=5,error_kw=dict(elinewidth=1, capthick=1)
                                            )
                    index = index+barWidth
                    i+=1

                plt.ylabel(product+" Yield (g/g)")
                ymin, ymax = plt.ylim()
                plt.ylim([0,ymax])

                endPointTiterLabel.sort()

                xticklabel = ''
                for attribute in ['strainID','identifier1','identifier2']:
                    if attribute != sortBy:
                        xticklabel = xticklabel+attribute

                if 'strainID' == sortBy:
                    tempticks =[self.replicateExperimentObjectDict[key].runIdentifier.identifier1+'+'+
                                self.replicateExperimentObjectDict[key].runIdentifier.identifier2 for key in strainsToPlot
                                if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == maxIndex]
                if 'identifier1' == sortBy:
                    tempticks = [self.replicateExperimentObjectDict[key].runIdentifier.strainID +'+'+
                                 self.replicateExperimentObjectDict[key].runIdentifier.identifier2 for key in strainsToPlot
                                 if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == maxIndex]
                if 'identifier2' == sortBy:
                    tempticks = [self.replicateExperimentObjectDict[key].runIdentifier.strainID +'+'+
                                 self.replicateExperimentObjectDict[key].runIdentifier.identifier1 for key in strainsToPlot
                                 if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == maxIndex]
                tempticks.sort()



                plt.xticks(index-0.4, tempticks, rotation='45', ha='right', va='top')

                ax.yaxis.set_ticks_position('left')
                ax.xaxis.set_ticks_position('bottom')
            figManager = plt.get_current_fig_manager()
            figManager.window.showMaximized()
            plt.tight_layout()
            plt.subplots_adjust(right=0.875)
            plt.legend([handle[key][0] for key in uniques],uniques,bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0)



        if withLegend == 0:
            plt.figure(figsize=(6, 3))
            for product in titersToPlot:
                endPointTiterAvg = []
                endPointTiterStd = []
                endPointTiterLabel = []
                pltNum += 1
                #ax = plt.subplot(0.8)
                ax = plt.subplot(1,len(replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products),pltNum)
                ax.spines["top"].set_visible(False)
                #ax.spines["bottom"].set_visible(False)
                ax.spines["right"].set_visible(False)
                #ax.spines["left"].set_visible(False)
                location = 0
                index = np.arange(len(strainsToPlot))

                strainsToPlot.sort()

                for key in strainsToPlot:
                    endPointTiterLabel.append(key)
                    endPointTiterAvg.append(replicateExperimentObjectList[key].avg.yields[product][-1])
                    endPointTiterStd.append(replicateExperimentObjectList[key].std.yields[product][-1])

                handle[key] = plt.bar(index,endPointTiterAvg,barWidth,yerr=endPointTiterStd,color=plt.get_cmap('Set2')(0.25),ecolor='black',capsize=5,error_kw=dict(elinewidth=1, capthick=1) )
                location += barWidth
                plt.xlabel("Time (hours)")
                plt.ylabel(product+" Yield (g/g)")
                ymin, ymax = plt.ylim()
                plt.ylim([0,ymax])
                plt.tight_layout()
                endPointTiterLabel.sort()
                plt.xticks(index + barWidth/2, endPointTiterLabel,rotation='45', ha='right', va='top')
                ax.yaxis.set_ticks_position('left')
                ax.xaxis.set_ticks_position('bottom')

        if withLegend == 1:
            plt.figure(figsize=(6, 2))

            for product in replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products:
                endPointTiterAvg = []
                endPointTiterStd = []
                endPointTiterLabel = []
                pltNum += 1
                ax = plt.subplot(1,len(replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products),pltNum)
                ax.spines["top"].set_visible(False)
                #ax.spines["bottom"].set_visible(False)
                ax.spines["right"].set_visible(False)
                #ax.spines["left"].set_visible(False)
                location = 0
                index = np.arange(len(strainsToPlot))

                for key in strainsToPlot:
                    endPointTiterLabel.append(key)
                    endPointTiterAvg.append(replicateExperimentObjectList[key].avg.yields[product][-1])
                    endPointTiterStd.append(replicateExperimentObjectList[key].std.yields[product][-1])

                barList = plt.bar(index,endPointTiterAvg,barWidth,yerr=endPointTiterStd,ecolor='k')
                count = 0
                for bar, count in zip(barList, range(len(strainsToPlot))):
                    bar.set_color(colors[count])
                location += barWidth
                plt.ylabel(product+" Titer (g/L)")
                ymin, ymax = plt.ylim()
                plt.ylim([0,ymax])
                plt.tight_layout()
                plt.xticks([])
                ax.yaxis.set_ticks_position('left')
                ax.xaxis.set_ticks_position('bottom')
            plt.subplots_adjust(right=0.7)
            plt.legend(barList,strainsToPlot,bbox_to_anchor=(1.15, 0.5), loc=6, borderaxespad=0)

    def printYieldTimeCourse(self, strainsToPlot):
        replicateExperimentObjectList = self.replicateExperimentObjectDict
        # You typically want your plot to be ~1.33x wider than tall. This plot is a rare
        # exception because of the number of lines being plotted on it.
        # Common sizes: (10, 7.5) and (12, 9)
        plt.figure(figsize=(12, 3))

        handle = dict()
        barWidth = 0.9/len(strainsToPlot)
        #plt.hold(False)
        pltNum = 0
        colors = plt.get_cmap('Paired')(np.linspace(0,1.0,len(strainsToPlot)))
        for product in replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products:
            pltNum += 1
            ax = plt.subplot(1,len(replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products)+1,pltNum)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            location = 0
            colorIndex = 0
            for key in strainsToPlot:
                index = np.arange(len(replicateExperimentObjectList[key].t))
                handle[key] = plt.bar(index+location,replicateExperimentObjectList[key].avg.yields[product],barWidth,yerr=replicateExperimentObjectList[key].std.yields[product],color=colors[colorIndex],ecolor='k')
                plt.xticks(index + barWidth, replicateExperimentObjectList[key].t)
                location += barWidth
                colorIndex += 1
                # print(replicateExperimentObjectList[key].avg.products[product].rate)
                # handle[key] = plt.plot(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50),
                #                                    replicateExperimentObjectList[key].avg.products[product].returnCurveFitPoints(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50)),'-',lw=2.5)
            plt.xlabel("Time (hours)")
            plt.ylabel(product+" Yield (g/g)")
            ymin, ymax = plt.ylim()
            plt.ylim([0,1])
            plt.tight_layout()
        #plt.subplot(1,4,4)
        plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.15, 0.5), loc=6, borderaxespad=0)
        plt.subplots_adjust(right=1.05)

    def printAllReplicateTimeCourse(self, figHandle=[], strainToPlot=[]):

        if figHandle == []:
            figHandle = plt.figure(figsize=(9, 5))

        plt.clf()
        if len(strainToPlot) > 1:
            strainToPlot = self.getAllStrains()[0]
        for singleExperiment in self.replicateExperimentObjectDict[strainToPlot[0]].singleTrialList:
            plt.plot(singleExperiment.OD.timeVec,singleExperiment.OD.dataVec)
        plt.ylabel(singleExperiment.runIdentifier.returnUniqueID())
        # plt.tight_layout()

class RunIdentifier(object):
    #Base RunIdentifier object
    def __init__(self):
        self.strainID = ''          # e.g. MG1655 dlacI
        self.identifier1 = ''       # e.g. pTOG009
        self.identifier2 = ''       # e.g. IPTG
        self.replicate = None       # e.g. 1
        self.time = -1            # e.g. 0
        self.titerName = 'None'     # e.g. Lactate
        self.titerType = 'None'     # e.g. titer or OD

        # self.temp = {'type':''}

    def getRunIdentifier(self, row):
        if type("asdf") == type(row):
            tempParsedIdentifier = row.split(',')
            if len(tempParsedIdentifier) == 0:
                print(tempParsedIdentifier," <-- not processed")
            if len(tempParsedIdentifier) > 0 :
                self.strainID = tempParsedIdentifier[0]
            if len(tempParsedIdentifier) > 1 :
                self.identifier1 = tempParsedIdentifier[1]
            if len(tempParsedIdentifier) > 2 :
                self.identifier2 = tempParsedIdentifier[2]
            if len(tempParsedIdentifier) > 3 :
                try:
                    self.replicate = int(tempParsedIdentifier[3])
                except:
                    print("Couldn't parse replicate from ",tempParsedIdentifier)

    def returnUniqueID_singleExperiment(self):
        return self.strainID+self.identifier1+self.identifier1+str(self.replicate)+self.titerName+self.titerType

    def returnUniqueID(self):
        return self.strainID+self.identifier1+self.identifier2

    def returnUniqueExptID(self):
        return self.strainID+self.identifier1+self.identifier2+str(self.replicate)

class TimePoint(object):
    def __init__(self, runID, titerName, t, titer):
        self.runIdentifier = runID
        self.titerName = titerName
        self. t = t
        self.titer = titer
        self.units = {'t': 'h',
                      'titer': 'g'}

    def getUniqueTimePointID(self):
        return self.runIdentifier.strainID+self.runIdentifier.identifier1+self.runIdentifier.identifier2+str(self.runIdentifier.replicate)+self.runIdentifier.titerName

class Titer(object):
    def __init__(self):
        self.timePointList = []
        self._runIdentifier = RunIdentifier()

    @property
    def runIdentifier(self):
        return self._runIdentifier

    @runIdentifier.setter
    def runIdentifier(self, runIdentifier):
        self._runIdentifier = runIdentifier

    def addTimePoint(self, timePoint):
        raise(Exception("No addTimePoint method defined in the child"))

    def getTimeCourseID(self):
        if len(self.timePointList)>0:
            return self.timePointList[0].runIdentifier.strainID+\
                   self.timePointList[0].runIdentifier.identifier1+\
                   self.timePointList[0].runIdentifier.identifier2+\
                   str(self.timePointList[0].runIdentifier.replicate)
        elif self.runIdentifier.strainID != '':
            return self.runIdentifier.strainID+\
                   self.runIdentifier.identifier1+\
                   self.runIdentifier.identifier2+\
                   str(self.runIdentifier.replicate)
        else:
            raise Exception("No unique ID or time points in Titer()")

    def getReplicateID(self):
        return self.runIdentifier.strainID+self.runIdentifier.identifier1+self.runIdentifier.identifier2

    def saveToDB(self, dbName):
        # Initialize database
        conn = sql.connect(dbName)
        c = conn.cursor()

        c.execute("""\
            INSERT INTO experiment

        """)


        c.execute("""\
           INSERT INTO TimeCourseTable
           (importDate TEXT, runStartDate TEXT, runEndDate TEXT, principalScientistName TEXT,
           secondaryScientistName TEXT, mediumBase TEXT, mediumSupplements TEXT, notes TEXT,
           strainID TEXT, identifier1 TEXT, identifier2 TEXT, identifier3 TEXT, replicate INTEGER,
           titerType TEXT, titerName TEXT, titerID TEXT, timeVec BLOB, dataVec BLOB)
        """)    #TODO

        conn.commit()
        c.close()
        conn.close()

class CurveFitObject(object):
    """
    Wrapper for curve fitting objects

    Parameters:
        paramList: List of parameters, with initial guess, max and min values
            Each parameter is a dict with the following form
                {'name': str PARAMETER NAME,

                'guess': float or lambda function

                'max': float or lambda function

                'min': float or lambda function

                'vary' True or False}

        growthEquation: A function to fit with the following form:
            def growthEquation(t, param1, param2, ..): return f(param1,param2,..)
    """
    def __init__(self,paramList,growthEquation):
        self.paramList = paramList
        self.growthEquation = growthEquation
        self.gmod = Model(growthEquation)

    def calcFit(self, t, data, method='slsqp'):
        for param in self.paramList:
            # print(param)
            # Check if the parameter is a lambda function
            temp = dict()
            for hint in ['guess','min','max']:
                # print('hint: ',hint,'param[hint]: ',param[hint])
                if type(param[hint]) == type(lambda x: 0):
                    temp[hint] = param[hint](data)
                else:
                    temp[hint] = param[hint]
            self.gmod.set_param_hint(param['name'],
                                     value=temp['guess'],
                                     min=temp['min'],
                                     max=temp['max'])
            # self.gmod.print_param_hints()

        try:
            params = self.gmod.make_params()
        except Exception as e:
            # self.gmod.print_param_hints()
            print(data)
            print(e)

        result = self.gmod.fit(data,params,t=t,method=method)
        return result

class TimeCourse(Titer):
    """
    Child of :class:`~Titer` which contains curve fitting relevant to time course data
    """
    def __init__(self, removeDeathPhaseFlag = False, useFilteredData = False):
        Titer.__init__(self)
        self.timeVec = None
        self._dataVec = None
        self.rate = None

        # Parameters
        self.removeDeathPhaseFlag = removeDeathPhaseFlag
        self.useFilteredDataFlag = useFilteredData
        self.deathPhaseStart = None
        self.blankSubtractionFlag = True


        self.savgolFilterWindowSize = 21    # Must be odd

        # Declare some standard curve fitting objects here
        self.curveFitObjectDict = dict()
        def growthEquation(t, A, B, C, Q, K, nu): return A + ((K-A)/(np.power((C+Q*np.exp(-B*t)),(1/nu))))
        keys = ['name','guess','min','max','vary']
        self.curveFitObjectDict['logisticGrowth'] = CurveFitObject(
                                        [dict(zip(keys,['A',np.min,lambda data: 0.975*np.min(data),lambda data:1.025*np.min(data),True])),
                                        dict(zip(keys,['B',lambda data: 0.5, lambda data: 0.001, lambda data: 1,True])),
                                        dict(zip(keys,['C',1,None,None,True])),
                                        dict(zip(keys,['Q',0.01,None,None,True])),
                                        dict(zip(keys,['K',max,lambda data: 0.975*max(data),lambda data: 1.025*max(data),True])),
                                        dict(zip(keys,['nu',1,None,None,True]))],
                                        growthEquation
                                        )

        # Declare the default curve fit
        self.fitType = 'logisticGrowth'

    @property
    def timeVec(self):
        return self._timeVec

    @timeVec.setter
    def timeVec(self, timeVec):
        self._timeVec = np.array(timeVec)

    @property
    def dataVec(self):
        if self.useFilteredDataFlag == True:
            return savgol_filter(self._dataVec,self.savgolFilterWindowSize,3)
        else:
            return self._dataVec

    @dataVec.setter
    def dataVec(self, dataVec):
        self._dataVec = np.array(dataVec)
        self.deathPhaseStart = len(dataVec)

        if self.removeDeathPhaseFlag == True:
            if np.max(dataVec) > 0.2:
                try:
                    if self.useFilteredDataFlag == True:
                        filteredData = savgol_filter(dataVec,51,3)
                    else:
                        filteredData = np.array(self._dataVec)
                    diff = np.diff(filteredData)

                    count=0
                    flag = 0

                    for i in range(len(diff)-10):
                        if diff[i] < 0:
                            flag = 1
                            count+=1
                            if count > 10:
                                self.deathPhaseStart = i-10
                                break
                        elif count > 0:
                            count = 1
                            flag = 0
                    # if flag == 0:
                    #     self.deathPhaseStart = len(dataVec)
                        # self._dataVec = dataVec
                    # print(len(self._dataVec)," ",len(self.timeVec))
                    # plt.plot(self._dataVec[0:self.deathPhaseStart],'r.')
                    # plt.plot(self._dataVec,'b-')
                    # plt.show()
                except Exception as e:
                    print(e)
                    print(dataVec)
                    # self.deathPhaseStart = len(dataVec)

            if self.deathPhaseStart == 0:
                 self.deathPhaseStart = len(self.dataVec)

        if len(self.dataVec)>5:
            self.calcExponentialRate()

    def commitToDB(self, singleTrialID, c = None):
        c.execute("""INSERT INTO timeCourseTable(singleTrialID, titerType, titerName, timeVec, dataVec, rate) VALUES (?, ?, ?, ?, ?, ?)""",
                  (singleTrialID,self.runIdentifier.titerType,self.runIdentifier.titerName,self.timeVec.dumps(),
                   self.dataVec.dumps(),pickle.dumps(self.rate))
        )

    def returnCurveFitPoints(self, t):
       return self.curveFitObjectDict[self.fitType].growthEquation(np.array(t), *self.rate)

    def addTimePoint(self, timePoint):
        self.timePointList.append(timePoint)
        if len(self.timePointList) == 1:
            self.runIdentifier = timePoint.runIdentifier
        else:
            for i in range(len(self.timePointList)-1):
                if self.timePointList[i].runIdentifier.returnUniqueID_singleExperiment() != self.timePointList[i+1].runIdentifier.returnUniqueID_singleExperiment():
                    raise Exception("runIdentifiers don't match within the timeCourse object")

        self.timePointList.sort(key=lambda timePoint: timePoint.t)
        self.timeVec = np.array([timePoint.t for timePoint in self.timePointList])
        self.dataVec = np.array([timePoint.titer for timePoint in self.timePointList])
        if len(self.timePointList)>6:
            self.calcExponentialRate()
        else:
            self.rate = [0,0,0,0,0,0]

    def calcExponentialRate(self):
        if self.runIdentifier.titerType == 'titer' or self.runIdentifier.titerType == 'substrate' or self.runIdentifier.titerType == 'product':
            print('Curve fitting for titers unimplemented in restructured curve fitting. Please see Depricated\depicratedCurveFittingCode.py')
            # gmod.set_param_hint('A', value=np.min(self.dataVec))
            # gmod.set_param_hint('B',value=2)
            # gmod.set_param_hint('C', value=1, vary=False)
            # gmod.set_param_hint('Q', value=0.1)#, max = 10)
            # gmod.set_param_hint('K', value = max(self.dataVec))#, max=5)
            # gmod.set_param_hint('nu', value=1, vary=False)
        elif self.runIdentifier.titerType == 'OD':
            # print('DPS: ',self.deathPhaseStart)
            # print(self.dataVec)
            result = self.curveFitObjectDict[self.fitType].calcFit(self.timeVec[0:self.deathPhaseStart], self.dataVec[0:self.deathPhaseStart], method = 'slsqp')
            self.rate = [0,0,0,0,0,0]
            for i, key in enumerate(result.best_values):
                if key == 'A':
                    self.rate[0] = result.best_values[key]
                if key == 'B':
                    self.rate[1] = result.best_values[key]
                if key == 'C':
                    self.rate[2] = result.best_values[key]
                if key == 'Q':
                    self.rate[3] = result.best_values[key]
                if key == 'K':
                    self.rate[4] = result.best_values[key]
                if key == 'nu':
                    self.rate[5] = result.best_values[key]
        else:
            print('Unidentified titer type:'+self.runIdentifier.titerType)


    def getFitParameters(self):
        return [[param['name'], self.rate[i]] for i, param in enumerate(self.curveFitObjectDict[self.fitType].paramList)]
        # if len(self.dataVec)>10:
        #     print(result.best_values)
        #     print(self.rate)

            # plt.plot(self.timeVec,y, 'bo')
            # #plt.plot(self.timeVec,  result.init_fit,'k--')
            # #plt.plot(self.timeVec, result.best_fit,'r-')
            # plt.plot(self.timeVec,self.returnCurveFitPoints(self.timeVec),'g-')
            # print(self.returnCurveFitPoints(self.timeVec))
            # plt.show()

class TimeCourseShell(TimeCourse):
    """
    This is a shell of :class:`~Titer' with an overidden setter to be used as a container
    """
    @TimeCourse.dataVec.setter
    def dataVec(self, dataVec):
        self._dataVec = dataVec

    def commitToDB(self, singleTrialID, c = None, stat = None):
        # print(self.runIdentifier.titerType)
        # print(self.runIdentifier.titerName)
        # print(self.timeVec)
        # print(self.dataVec)
        if stat == None:
            raise Exception('Cannot commit to db with defined statistic')
        c.execute("""INSERT INTO timeCourseTable_"""+stat+"""(singleTrial_"""+stat+"""ID, titerType, titerName, dataVec, rate) VALUES (?, ?, ?, ?, ?)""",
                  (singleTrialID,self.runIdentifier.titerType,self.runIdentifier.titerName,
                   self.dataVec.dumps(),pickle.dumps(self.rate))
        )
class EndPoint(Titer):
    """
    This is a child of :class:`~Titer` which does not calcualte any time-based data
    """
    def __init__(self, runID, t, data):
        Titer.__init__(self, runID, t, data)

    def addTimePoint(self, timePoint):
        if len(self.timePointList) < 2:
            self.timePointList.append(timePoint)
        else:
            raise Exception("Cannot have more than two timePoints for an endPoint Object")

        if len(self.timePointList) == 2:
            self.timePointList.sort(key=lambda timePoint: timePoint.t)


class SingleTrial(object):
    """
    Container for single experiment data. This includes all data for a single strain (OD, titers, fluorescence, etc.)
    """
    def __init__(self):
        self._t = np.array([])
        self.titerObjectList = dict()

        self.ODKey = None
        self.productKeys = []
        self.substrateKey = None
        self.fluorescenceKeys = None

        self.runIdentifier = RunIdentifier()

        self._OD = None
        self._substrate = None
        self._products = dict()
        self._fluorescence = dict()

        self.yields = dict()

    # Setters and Getters
    @property
    def OD(self):
        return self._OD

    @OD.setter
    def OD(self, OD):
        self._OD = OD
        self.checkTimeVectors()

    @property
    def substrate(self):
        return self._substrate

    @substrate.setter
    def substrate(self, substrate):
        self._substrate = substrate
        self.checkTimeVectors()
        self.calcSubstrateConsumed()
        if self._products:
            self.calcYield()

    @property
    def t(self):
        return self._t

    @t.setter
    def t(self, t):
        self._t = t

    @property
    def products(self):
        return self._products

    @products.setter
    def products(self, products):
        self._products = products
        if self._substrate:
            self.calcYield()

    def commitToDB(self, replicateID, c = None):
        c.execute("""INSERT INTO singleTrialTable(replicateID, replicate, yieldsDict) VALUES (?, ?, ?)""",
                 (replicateID,self.runIdentifier.replicate,pickle.dumps(self.yields)))

        c.execute("""SELECT MAX(singleTrialID) from singleTrialTable""")
        singleTrialID = c.fetchall()[0][0]

        for titerType in ['OD','substrate']:
            if getattr(self,titerType) != None: getattr(self,titerType).commitToDB(singleTrialID, c=c)

        for key in self.products:
            self.products[key].commitToDB(singleTrialID, c = c)


    def loadFromDB(self, singleTrialID = None, c = None):
        c.execute("""SELECT yieldsDict FROM singleTrialTable WHERE singleTrialID == ?""",(singleTrialID,))
        data = c.fetchall()[0][0]
        self.yields = pickle.loads(data)

        for titerType in ['OD','substrate']:
            c.execute("""SELECT timeCourseID, singleTrialID, titerType, titerName, timeVec, dataVec, rate FROM
                    timeCourseTable WHERE singleTrialID == ? AND titerType == ?""",(singleTrialID,titerType))
            for row in c.fetchall():
                if titerType == 'OD':
                    self._OD = TimeCourse()
                    self._OD.runIdentifier.titerType = row[2]
                    self._OD.runIdentifier.titerName = row[3]
                    self._OD.timeVec = np.loads(row[4])
                    self._OD._dataVec = np.loads(row[5])
                if titerType == 'substrate':
                    self._substrate = TimeCourse()
                    self._substrate.runIdentifier.titerType = row[2]
                    self._substrate.runIdentifier.titerName = row[3]
                    self._substrate.timeVec = np.loads(row[4])
                    self._substrate._dataVec = np.loads(row[5])
                # setattr(self,'_'+titerType,TimeCourse())
                # setattr(self,'_'+titerType+'.runIdentifier.titerType',row[2])
                # setattr(self,'_'+titerType+'.runIdentifier.titerName',row[3])
                # setattr(self,'_'+titerType+'.timeVec',np.loads(row[4]))
                # setattr(self,'_'+titerType+'._dataVec',np.loads(row[5]))
                # print(np.loads(row[4]))

        c.execute("""SELECT timeCourseID, singleTrialID, titerType, titerName, timeVec, dataVec, rate FROM
                timeCourseTable WHERE singleTrialID == ? AND titerType = 'product'""",(singleTrialID,))
        for row in c.fetchall():
            key = row[3]
            self._products[key] = TimeCourse()
            self._products[key].runIdentifier.titerType = row[3]
            self._products[key].runIdentifier.titerName = row[4]
            self._products[key]._timeVec = np.loads(row[4])
            self._products[key]._dataVec = np.loads(row[5])
            self._products[key].rate = pickle.loads(row[6])

        self._t = self._OD.timeVec
        a = 2

    def calcMassBalance(self, OD_gdw = None, calculateFBACO2 = False):
        if calculateFBACO2 == True:
            import cobra

            # Load the COBRA model
            ...

            # Convert the common names to COBRA model names
            commonNameCobraDictionary = {'Lactate':...,
                                         'Ethanol':...,
                                         'Acetate':...,
                                         'Formate':...,
                                         'Glycolate':...,
                                         'Glucose':...,
                                         'Succinate':...
                                         }

            # Get the molar mass from COBRA model and covert the grams to mmol
            substrate = model.metabolites.get_by_id(substrate_name)
            # substrate_mmol = substrate.formulaWeight()
            # substrate.lower_bound = self.substrate.dataVec[-1]
            # substrate.upper_bound = self.substrate.dataVec[-1]
            productsCOBRA = dict()
            for key in self.yields:
                modelMetID = commonNameCobraDictionary[key]
                productsCOBRA[key] = model.metabolites.get_by_id(modelMetID)

            # Set the bounds
            ...

            # Run the FBA and return the CO2
            ...

        if type(OD_gdw) == None:
            # Parameters for E. coli
            OD_gdw = 0.33 # Correlation for OD to gdw for mass balance

        #self.substrateConsumed

        if self.OD is not None:
            # Calc mass of biomass
            biomass_gdw = self._OD.dataVec/OD_gdw
        else:   biomass_gdw = None

        # Calculate the mass of products consumed
        totalProductMass = np.sum([self.products[productKey].dataVec for productKey in self.products],axis=0)

        # Calculate the mass balance (input-output)
        if biomass_gdw is None:   biomass_gdw = np.zeros([len(self.substrateConsumed)])   # If this isn't defined, set biomass to zero
        massBalance = self.substrateConsumed - totalProductMass - biomass_gdw

        return {'substrateConsumed':self.substrateConsumed,
                'totalProductMass':totalProductMass,
                'biomass_gdw':biomass_gdw,
                'massBalance': massBalance}

    def addTiterObject(self, titerObject):
        if titerObject.runIdentifier.titerType == 'substrate':
            self.titerObjectList[titerObject.runIdentifier.titerName] = titerObject
            self._substrate = titerObject
            self.substrateKey = titerObject.runIdentifier.titerName
            self.calcSubstrateConsumed()

        if titerObject.runIdentifier.titerType == 'OD':
            self.titerObjectList[titerObject.runIdentifier.titerName] = titerObject
            self._OD = titerObject
            self.ODKey = titerObject.runIdentifier.titerName

        if titerObject.runIdentifier.titerType == 'product':
            self.titerObjectList[titerObject.runIdentifier.titerName] = titerObject
            self._products[titerObject.runIdentifier.titerName] = titerObject
            self.productKeys.append(titerObject.runIdentifier.titerName)

        if titerObject.runIdentifier.titerType == 'fluorescence':
            self.titerObjectList[titerObject.runIdentifier.titerName] = titerObject
            self._fluorescence[titerObject.runIdentifier.titerName] = titerObject
            self.fluorescenceKeys.append(titerObject.runIdentifier.titerName)

        if self.substrateKey != None and len(self.productKeys)>0:
            self.calcYield()

        self.checkTimeVectors()
        self.runIdentifier = titerObject.runIdentifier
        self.runIdentifier.time = None

    def checkTimeVectors(self):
        checkTimeVectorsFlag = 1
        if checkTimeVectorsFlag == 1:
            t = []
            flag = 0
            if self.OD:
                self._t = self.OD.timeVec
                t.append(self.OD.timeVec)

            if self.substrate:
                self._t = self.substrate.timeVec
                t.append(self.substrate.timeVec)

            if self.products:
                for key in self.products:
                    self._t = self.products[key].timeVec
                    t.append(self.products[key].timeVec)

            for i in range(len(t)-1):
                if (t[i] != t[i+1]).all():
                    flag = 1

            if flag==1:
                raise(Exception("Time vectors within an experiment don't match, must implement new methods to deal with this type of data (if even possible)"))

    def getUniqueTimePointID(self):
        return self.substrate.runIdentifier.strainID+self.substrate.runIdentifier.identifier1+self.substrate.runIdentifier.identifier2+str(self.substrate.runIdentifier.replicate)

    def getUniqueReplicateID(self):
        return self.titerObjectList[list(self.titerObjectList.keys())[0]].getReplicateID()

    def calcSubstrateConsumed(self):
        self.substrateConsumed = np.empty([len(self.substrate.dataVec)])
        for timePointIndex in range(len(self.substrate.timeVec)):
            self.substrateConsumed[timePointIndex] = self.substrate.dataVec[0]-self.substrate.dataVec[timePointIndex]

    def calcYield(self):
        self.yields = dict()
        for productKey in self.products:
            self.yields[productKey] = np.divide(self.products[productKey].dataVec,self.substrateConsumed)

class SingleTrialDataShell(SingleTrial):
    """
    Object which overwrites the SingleTrial objects setters and getters, acts as a shell of data with the
    same structure as SingleTrial
    """

    def __init__(self):
        SingleTrial.__init__(self)

    @SingleTrial.substrate.setter
    def substrate(self, substrate):
        self._substrate = substrate

    @SingleTrial.OD.setter
    def OD(self, OD):
        self._OD = OD

    @SingleTrial.products.setter
    def products(self, products):
        self._products = products

    def commitToDB(self, replicateID, c = None, stat = None):
        if stat == None:
            raise Exception('Cannot commit a statistic to the database without specifying which stat (mean/std)')
        else:
            c.execute("""INSERT INTO singleTrialTable_"""+stat+"""(replicateID, replicate, yieldsDict) VALUES (?, ?, ?)""",
                     (replicateID,self.runIdentifier.replicate,pickle.dumps(self.yields)))
            c.execute("""SELECT MAX(singleTrialID_"""+stat+""") from singleTrialTable_"""+stat)

            singleTrialID = c.fetchall()[0][0]

            for titerType in ['OD','substrate']:
                print(titerType)
                print(type(getattr(self,titerType)))
                if titerType == 'substrate':
                    print(getattr(self,titerType))
                if getattr(self,titerType) != None: getattr(self,titerType).commitToDB(singleTrialID, c=c, stat = stat)
            for key in self.products:
                self.products[key].commitToDB(singleTrialID, c = c, stat = stat)






    def loadFromDB(self, singleTrialID = None, c = None, stat = None):
        if stat == None:
            raise Exception('Cannot commit a statistic to the database without specifying which stat (mean/std)')

        c.execute("""SELECT yieldsDict FROM singleTrialTable_"""+stat+""" WHERE singleTrialID_"""+stat+""" == ?""",(singleTrialID,))
        temp = c.fetchall()
        # try:
        data = temp[0][0]
        # except Exception as e:
        #     print(e)
        #     print(temp)
        #     print(singleTrialID)
        #     a = 2
        self.yields = pickle.loads(data)

        for titerType in ['OD','substrate']:
            c.execute("""SELECT timeCourseID, singleTrial_"""+stat+"""ID, titerType, titerName, dataVec, rate FROM
                    timeCourseTable_"""+stat+""" WHERE singleTrial_"""+stat+"""ID == ? AND titerType = ?""",(singleTrialID,titerType))
            for row in c.fetchall():
                if titerType == 'OD':
                    self._OD = TimeCourse()
                    self._OD.runIdentifier.titerType = row[2]
                    self._OD.runIdentifier.titerName = row[3]
                    self._OD._dataVec = np.loads(row[4])
                    self._OD.rate = pickle.loads(row[5])
                if titerType == 'substrate':
                    self._substrate = TimeCourse()
                    self._substrate.runIdentifier.titerType = row[2]
                    self._substrate.runIdentifier.titerName = row[3]
                    self._substrate._dataVec = np.loads(row[4])
                    self._substrate.rate = pickle.loads(row[5])

        c.execute("""SELECT timeCourseID, singleTrial_"""+stat+"""ID, titerType, titerName, dataVec, rate FROM
                timeCourseTable_"""+stat+""" WHERE singleTrial_"""+stat+"""ID == ? AND titerType = "product" """,(singleTrialID,))

        for row in c.fetchall():
            key = row[3]
            self._products[key] = TimeCourse()
            self._products[key].runIdentifier.titerType = row[2]
            self._products[key].runIdentifier.titerName = row[3]
            self._products[key]._dataVec = np.loads(row[4])
            self._products[key].rate = pickle.loads(row[5])

class ReplicateTrial(object):
    """
    This object stores SingleTrial objects and calculates statistics on these replicates for each of the
    titers which are stored within it
    """
    def __init__(self):
        self.avg = SingleTrialDataShell()
        self.std = SingleTrialDataShell()
        self.t = None
        self.singleTrialList = []
        self.runIdentifier = RunIdentifier()
        self.badReplicates = []
        self.replicateIDs = []
        #self.checkReplicateUniqueIDMatch()

    def commitToDB(self, experimentID = None, c = None):
        if experimentID == None:
            print('No experiment ID selected')
        else:
            identifier3 = ''
            c.execute("""\
               INSERT INTO replicateTable(experimentID, strainID, identifier1, identifier2, identifier3)
               VALUES (?, ?, ?, ?, ?)""",
               (experimentID,self.runIdentifier.strainID,self.runIdentifier.identifier1,
               self.runIdentifier.identifier2,identifier3)
            )
            c.execute("""SELECT MAX(replicateID) FROM replicateTable""")
            replicateID = c.fetchall()[0][0]


            for singleExperiment in self.singleTrialList:
                singleExperiment.commitToDB(replicateID, c = c)
            self.avg.commitToDB(replicateID, c = c, stat='avg')
            self.std.commitToDB(replicateID, c = c, stat='std')

    def loadFromDB(self, c = None, replicateID = 'all'):
        # conn = sql.conenct(dbName)
        # c = conn.cursor()
        if type(replicateID) is not (int): raise Exception('Cannot load multiple replicates in a single call to this function, load from parent instead')
        c.execute("""SELECT * FROM replicateTable WHERE replicateID = ?""",(replicateID,))
        for row in c.fetchall():
            self.runIdentifier.strainID = row[2]
            self.runIdentifier.identifier1 = row[3]
            self.runIdentifier.identifier2 = row[4]

        c.execute("""SELECT singleTrialID, replicateID, replicate, yieldsDict FROM singleTrialTable WHERE replicateID = ?""",(replicateID,))
        for row in c.fetchall():
            self.singleTrialList.append(SingleTrial())
            self.singleTrialList[-1].yields = pickle.loads(row[3])
            self.singleTrialList[-1].runIdentifier.replicate = row[2]
            self.singleTrialList[-1].loadFromDB(c = c, singleTrialID = row[0])
        self.t = self.singleTrialList[0].t

        for stat in ['_avg','_std']:
            c.execute("""SELECT singleTrialID"""+stat+""", replicateID, replicate, yieldsDict FROM singleTrialTable"""+stat+""" WHERE replicateID = ?""",(replicateID,))
            row = c.fetchall()[0]
            getattr(self,stat.replace('_','')).loadFromDB(c = c, singleTrialID = row[0], stat = stat.replace('_',''))
            #TODO MUST FINISH THIS

    def checkReplicateUniqueIDMatch(self):
        for i in range(len(self.singleTrialList)-1):
            if self.singleTrialList[i].getUniqueReplicateID() != self.singleTrialList[i+1].getUniqueReplicateID():
                raise Exception("the replicates do not have the same uniqueID, either the uniqueID includes too much information or the strains don't match")

            if (self.singleTrialList[i].t != self.singleTrialList[i+1].t).all():
                print(self.singleTrialList[i].t,self.singleTrialList[i].t)
                raise Exception("time vectors don't match within replicates")
            else:
                self.t = self.singleTrialList[i].t

            if len(self.singleTrialList[i].t) != len(self.singleTrialList[i+1].t): #TODO
                print("Time Vector 1: ",self.singleTrialList[i].t,"\nTime Vector 2: ",self.singleTrialList[i+1].t)
                print("Vector 1: ",self.singleTrialList[i].substrate.dataVec,"\nVector 2: ",self.singleTrialList[i+1].substrate.dataVec)
                raise(Exception("length of substrate vectors do not match"))

            for key in self.singleTrialList[i].products:
                if len(self.singleTrialList[i].products[key].dataVec) != len(self.singleTrialList[i+1].products[key].dataVec):
                    raise(Exception("length of product vector "+str(key)+" do not match"))

    def addReplicateExperiment(self, newReplicateExperiment):
        """
        Add a SingleTrial object to this list of replicates

        mewReplicateExperiment: A :class:`~SingleTrial` object
        """
        self.singleTrialList.append(newReplicateExperiment)
        if len(self.singleTrialList)==1:
            self.t = self.singleTrialList[0].t
        self.checkReplicateUniqueIDMatch()

        self.runIdentifier = newReplicateExperiment.runIdentifier
        self.runIdentifier.time = None
        self.replicateIDs.append(newReplicateExperiment.runIdentifier.replicate)    #TODO remove this redundant functionality
        self.replicateIDs.sort()
        self.calcAverageAndDev()


    def calcAverageAndDev(self):
        """
        Calculates the statistics on the SingleTrial objects
        """

        # First, check what data exists
        ODflag = 0
        productFlag = 0
        substrateFlag = 0
        yieldFlag = 0

        for singleExperiment in self.singleTrialList:
            if singleExperiment.OD:
                ODflag = 1
            if singleExperiment.products:
                productFlag = 1 #TODO need to make generic for different products in different expts
            if singleExperiment.substrate:
                substrateFlag=1
            if singleExperiment.yields:
                yieldFlag = 1

        # Then, calculate statistics for available data
        if ODflag == 1:
            # Place this data in a shell, with no setters and getters
            self.avg.OD = TimeCourseShell()
            self.std.OD = TimeCourseShell()
            self.avg.OD.timeVec = self.t

            # Remove replicates which significantly increase the standard deviation
            if len(self.replicateIDs) > 2:
                tempRate = dict()
                for testReplicate in self.replicateIDs:
                    tempRate[testReplicate] = np.sum(np.std([singleExperimentObject.OD.dataVec for singleExperimentObject in self.singleTrialList
                                                      if singleExperimentObject.runIdentifier.replicate != testReplicate], axis=0))   # Perform this test only on growth rate
                minDevKey = min(tempRate,key=tempRate.get)
                tempRateKey = minDevKey

                if tempRate[tempRateKey]/np.mean([tempRate[tempRateKey2] for tempRateKey2 in tempRate if tempRateKey2 != tempRateKey]) < 0.5 :
                    self.badReplicates.append(int(tempRateKey))
            self.badReplicates = []
            # Calculate the statistics on the data and parameters
            self.avg.OD.dataVec = np.mean([singleExperimentObject.OD.dataVec for singleExperimentObject in self.singleTrialList if singleExperimentObject.runIdentifier.replicate not in self.badReplicates], axis=0)
            self.std.OD.dataVec = np.std([singleExperimentObject.OD.dataVec for singleExperimentObject in self.singleTrialList if singleExperimentObject.runIdentifier.replicate not in self.badReplicates], axis=0)
            self.avg.OD.rate = np.mean([singleExperimentObject.OD.rate for singleExperimentObject in self.singleTrialList if singleExperimentObject.runIdentifier.replicate not in self.badReplicates], axis=0)
            self.std.OD.rate = np.std([singleExperimentObject.OD.rate for singleExperimentObject in self.singleTrialList if singleExperimentObject.runIdentifier.replicate not in self.badReplicates], axis=0)
            self.avg.OD.runIdentifier = self.singleTrialList[0].OD.runIdentifier
            self.std.OD.runIdentifier = self.singleTrialList[0].OD.runIdentifier

        if productFlag == 1:
            for key in self.singleTrialList[0].products:
                self.avg.products[key] = TimeCourseShell()
                self.std.products[key] = TimeCourseShell()
                self.avg.products[key].dataVec = np.mean([singleExperimentObject.products[key].dataVec for singleExperimentObject in self.singleTrialList],axis=0)
                self.std.products[key].dataVec = np.std([singleExperimentObject.products[key].dataVec for singleExperimentObject in self.singleTrialList],axis=0)

                # TODO: Reimplement this
                # self.avg.products[key].rate = np.mean([singleExperimentObject.products[key].rate for singleExperimentObject in self.singleTrialList],axis=0)

                # TODO: Probably need to remove soem data from the runIdentifier here
                self.avg.products[key].runIdentifier = self.singleTrialList[0].products[key].runIdentifier
                self.std.products[key].runIdentifier = self.singleTrialList[0].products[key].runIdentifier

                # self.avg.products.runIdentifier = singleTrialList[0].runIdentifier


        if substrateFlag == 1:
            self.avg.substrate = TimeCourseShell()
            self.std.substrate = TimeCourseShell()
            self.avg.substrate.dataVec = np.mean([singleExperimentObject.substrate.dataVec for singleExperimentObject in self.singleTrialList], axis=0)
            self.std.substrate.dataVec = np.std([singleExperimentObject.substrate.dataVec for singleExperimentObject in self.singleTrialList], axis=0)
            self.avg.substrate.runIdentifier = self.singleTrialList[0].substrate.runIdentifier
            self.std.substrate.runIdentifier = self.singleTrialList[0].substrate.runIdentifier

        if yieldFlag == 1:
            for key in self.singleTrialList[0].yields:
                self.avg.yields[key] = np.mean([singleExperimentObject.yields[key] for singleExperimentObject in self.singleTrialList],axis=0)
                self.std.yields[key] = np.std([singleExperimentObject.yields[key] for singleExperimentObject in self.singleTrialList],axis=0)


class projectContainer(object):
    def __init__(self):
        raise Exception('This function has been depricated, please use fDAPI.Experiment instead')