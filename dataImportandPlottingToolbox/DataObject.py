'''
Written by: Naveen Venyak
Date:       October, 2015

This is the main data object container. Almost all functionality is contained here.
'''

__author__ = 'Naveen Venayak'

import numpy as np
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt

from lmfit import Model
from pyexcel_xlsx import get_data

from PyQt4 import QtGui, QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar

import os
import time
import copy
import pickle
import sys

class Window(QtGui.QDialog):
    def __init__(self, newProjectContainer, parent=None):
        super(Window, self).__init__(parent)
        self.newProjectContainer = newProjectContainer

        # a figure instance to plot on
        self.figure = plt.figure()
        self.strainsToPlot = self.newProjectContainer.getAllStrains()
        self.titersToPlot = self.newProjectContainer.getAllTiters()
        self.sortBy = 'identifier1'
        self.plotType = 'printGenericTimeCourse'
        # self.newProjectContainer.printGrowthRateBarChart(self.figure,strainsToPlot=self.strainsToPlot)

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Just some button connected to `plot` method
        # self.button = QtGui.QPushButton('Plot')
        # self.button.clicked.connect(self.plot)

        comboBox = QtGui.QComboBox(self)
        comboBox.addItem('strainID')
        comboBox.addItem('identifier1')
        comboBox.addItem('identifier2')
        comboBox.activated[str].connect(self.updateSortBy)

        plotTypeComboBox = QtGui.QComboBox(self)
        plotTypeComboBox.addItem('printGenericTimeCourse')
        plotTypeComboBox.addItem('printGrowthRateBarChart')
        plotTypeComboBox.addItem('printAllReplicateTimeCourse')
        plotTypeComboBox.activated[str].connect(self.updatePlotType)

        self.checkBox = dict()
        for strain in self.strainsToPlot:
            self.checkBox[strain] = (QtGui.QCheckBox(strain,self))
            self.checkBox[strain].stateChanged.connect(self.updateStrainsToPlot)

        self.titersCheckBox = dict()
        for titer in self.titersToPlot:
            self.titersCheckBox[titer] = (QtGui.QCheckBox(titer,self))
            self.titersCheckBox[titer].stateChanged.connect(self.updateTiters)



        # set the layout

        leftVertLayout = QtGui.QVBoxLayout()
        leftVertLayout.addWidget(self.toolbar)
        leftVertLayout.addWidget(self.canvas)


        rightVertLayout = QtGui.QVBoxLayout()
        rightVertLayout.addWidget(plotTypeComboBox)
        rightVertLayout.addWidget(comboBox)
        for strainToPlot in self.strainsToPlot:
            rightVertLayout.addWidget(self.checkBox[strainToPlot])

        titersVertLayout = QtGui.QVBoxLayout()
        for titer in self.titersToPlot:
            titersVertLayout.addWidget(self.titersCheckBox[titer])

        horLayout = QtGui.QHBoxLayout()
        horLayout.addLayout(leftVertLayout)
        horLayout.addLayout(rightVertLayout)
        horLayout.addLayout(titersVertLayout)
        self.setLayout(horLayout)

    def updatePlotType(self, plotType):
        self.plotType = plotType
        self.updateFigure()

    def updateSortBy(self, sortBy):
        print('in here')
        self.sortBy = sortBy
        self.updateFigure()

    def updateStrainsToPlot(self):
        self.strainsToPlot = []
        for checkBoxKey in self.checkBox:
            if self.checkBox[checkBoxKey].checkState() == QtCore.Qt.Checked:
                self.strainsToPlot.append(checkBoxKey)
        self.updateFigure()

    def updateTiters(self):
        self.titersToPlot = []
        for titerCheckBoxKey in self.titersCheckBox:
            if self.titersCheckBox[titerCheckBoxKey].checkState() == QtCore.Qt.Checked:
                self.titersToPlot.append(titerCheckBoxKey)
        self.updateFigure()

    # def updateBadReplicates(self):
    #     for replicateCheckBoxKey in self.replicateCheckBox:



    def updateFigure(self):
        #getattr(self.newProjectContainer,self.plotType)(self.figure, self.strainsToPlot, self.sortBy)
        if self.plotType == 'printGenericTimeCourse':
            self.newProjectContainer.printGenericTimeCourse(figHandle=self.figure, strainsToPlot=self.strainsToPlot,titersToPlot=self.titersToPlot, removePointFraction=4, plotCurveFit=True)
        if self.plotType == 'printGrowthRateBarChart':
            self.newProjectContainer.printGrowthRateBarChart(self.figure, self.strainsToPlot, self.sortBy)
        if self.plotType == 'printAllReplicateTimeCourse':
            self.newProjectContainer.printAllReplicateTimeCourse(self.figure, self.strainsToPlot)
        self.canvas.draw()

class projectContainer(object):
    colorMap = 'Set3'

    def __init__(self):
        self.timePointList = []#dict()
        self.titerObjectDict = dict()
        self.singleExperimentObjectDict = dict()
        self.replicateExperimentObjectDict = dict()

    def plottingGUI(self):
        app = QtGui.QApplication(sys.argv)

        main = Window(self)
        main.show()

        sys.exit(app.exec_())

    def getAllStrains(self):
        temp = [key for key in self.replicateExperimentObjectDict if self.replicateExperimentObjectDict[key].runIdentifier.identifier1 != '']
        temp.sort()
        # print(temp)
        return temp

    def getAllTiters(self):
        titersToPlot = [[[product for product in singleExperiment.products] for singleExperiment in self.replicateExperimentObjectDict[key].singleExperimentList] for key in self.replicateExperimentObjectDict]

        # Flatten list and find the uniques
        titersToPlot = [y for x in titersToPlot for y in x]
        titersToPlot =  list(set([y for x in titersToPlot for y in x]))

        ODList = [[singleExperiment.OD for singleExperiment in self.replicateExperimentObjectDict[key].singleExperimentList] for key in self.replicateExperimentObjectDict]
        ODList = list(set([y for x in ODList for y in x]))

        # print(ODList)
        if ODList[0] != None:
            titersToPlot.append('OD')

        return titersToPlot

    def getTimeCourseData(self, strainName, titerName, replicate):
        pass

    def parseRawData(self, fileName, dataFormat):
        # Get data from xlsx file
        data = get_data(fileName)
        print('Imported data from %s' % (fileName))
        t0 = time.time()

        if dataFormat == 'NV_OD':
            # Check for correct data for import
            if 'OD' not in data.keys():
                raise Exception("No sheet named 'OD' found")
            else:
                ODDataSheetName = 'OD'

            # if 'titers' not in data.keys():
            #     raise Exception("No sheet named 'titers' found")

            # Parse data into timeCourseObjects
            skippedLines = 0
            timeCourseObjectList = dict()
            for row in data[ODDataSheetName][1:]:
                temp_run_identifier_object = runIdentifier()
                if type("asdf") == type(row[0]):
                    temp_run_identifier_object.getRunIdentifier(row[0])
                    temp_run_identifier_object.titerName = 'OD600'
                    temp_run_identifier_object.titerType = 'OD'
                    tempTimeCourseObject = timeCourseObject()
                    tempTimeCourseObject.runIdentifier = temp_run_identifier_object
                    # Data in seconds, data required to be in hours
                    tempTimeCourseObject.timeVec = np.array(np.divide(data[ODDataSheetName][0][1:], 3600))

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
                        tempRunIdentifierObject = runIdentifier()
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
                            self.timePointList.append(timePoint(copy.copy(tempRunIdentifierObject), key, tempRunIdentifierObject.t, data['titers'][i][titerNameColumn[key]]))

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
                    temp_run_identifier_object = runIdentifier()
                    temp_run_identifier_object.getRunIdentifier(data['titers'][i][0])

                    tempParsedIdentifier = data['titers'][i][0].split(',')  #Parse the string using comma delimiter

                    temp_run_identifier_object.t = 15.#tempParsedIdentifier[2]

                    for key in tempTimePointCollection:
                        temp_run_identifier_object.titerName = key
                        if key == 'Glucose':
                            temp_run_identifier_object.titerType = 'substrate'
                            self.timePointList.append(timePoint(copy.copy(temp_run_identifier_object), key, 0, 15))
                        else:
                            temp_run_identifier_object.titerType = 'product'
                            self.timePointList.append(timePoint(copy.copy(temp_run_identifier_object), key, 0, 0))
                        self.timePointList.append(timePoint(copy.copy(temp_run_identifier_object), key, temp_run_identifier_object.t, data['titers'][i][titerNameColumn[key]]))


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
                self.titerObjectDict[timePoint.getUniqueTimePointID()] = timeCourseObject()
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
                self.singleExperimentObjectDict[titerObjectDict[titerObjectDictKey].getTimeCourseID()] = singleExperimentData()
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
                self.replicateExperimentObjectDict[singleExperimentObjectList[key].getUniqueReplicateID()] = replicateExperimentObject()
                self.replicateExperimentObjectDict[singleExperimentObjectList[key].getUniqueReplicateID()].addReplicateExperiment(singleExperimentObjectList[key])
        tf = time.time()
        print("Parsed %i titer objects in %0.1fs\n" % (len(self.replicateExperimentObjectDict),(tf-t0)))

    def pickle(self, fileName):
        pickle.dump([self.timePointList, self.titerObjectDict, self.singleExperimentObjectDict, self.replicateExperimentObjectDict], open(fileName,'wb'))

    def unpickle(self, fileName):
        t0 = time.time()
        with open(fileName,'rb') as data:
            self.timePointList, self.titerObjectDict, self.singleExperimentObjectDict, self.replicateExperimentObjectDict = pickle.load(data)
        print('Read data from %s in %0.3fs' % (fileName,time.time()-t0))

    def printGenericTimeCourse(self, figHandle = [], strainsToPlot=[], titersToPlot=[], removePointFraction=1, shadeErrorRegion=False, showGrowthRates=True, plotCurveFit=True ):
        if figHandle == []:
            figHandle = plt.figure()

        figHandle.set_facecolor('w')

        if strainsToPlot == []:
            strainsToPlot = self.getAllStrains()
        # Plot all product titers if none specified TODO: Add an option to plot OD as well
        if titersToPlot == []:
            titersToPlot = self.getAllTiters()

        print(strainsToPlot,titersToPlot)

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

                    handle[key] = plt.plot(np.linspace(min(scaledTime),max(scaledTime),50),
                                            self.replicateExperimentObjectDict[key].avg.products[product].returnCurveFitPoints(np.linspace(min(self.replicateExperimentObjectDict[key].t),max(self.replicateExperimentObjectDict[key].t),50)),
                                           '-',lw=0.5,color=colors[colorIndex])

                    handle[key] = plt.errorbar(self.replicateExperimentObjectDict[key].t,self.replicateExperimentObjectDict[key].avg.products[product].dataVec,self.replicateExperimentObjectDict[key].std.products[product].dataVec,lw=2.5,elinewidth=1,capsize=2,fmt='o-',color=colors[colorIndex])
                    ylabel = product+" Titer (g/L)"

                colorIndex += 1

            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            ymin, ymax = plt.ylim()
            xmin, xmax = plt.xlim()
            plt.xlim([0,xmax*1.2])
            plt.ylim([0,ymax])
        plt.tight_layout()
        plt.tick_params(right="off",top="off")
        plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0, frameon=False)
        plt.subplots_adjust(right=0.7)

        if len(titersToPlot) == 1:
            plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0)
            plt.subplots_adjust(right=0.7)
        elif len(titersToPlot) < 4:
            plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0)
            plt.subplots_adjust(right=0.75)
        else:
            plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.05, 1.1), loc=6, borderaxespad=0)
            plt.subplots_adjust(right=0.75)

        # Save the figure
        plt.savefig(os.path.join(os.path.dirname(__file__),'Figures/'+time.strftime('%y')+'.'+time.strftime('%m')+'.'+time.strftime('%d')+" H"+time.strftime('%H')+'-M'+time.strftime('%M')+'-S'+time.strftime('%S')+'.png'))
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

        # uniques = list(set([getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) for key in strainsToPlot]))
        # uniques.sort()
        #
        # # Find max number of samples (in case they all aren't the same)
        # maxSamples = 0
        # for unique in uniques:
        #     if len([self.replicateExperimentObjectDict[key].avg.OD.rate[1] for key in strainsToPlot if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == unique]) > maxSamples:
        #         maxSamples = len([self.replicateExperimentObjectDict[key].avg.OD.rate[1] for key in strainsToPlot if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == unique])
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
                    # if len([self.replicateExperimentObjectDict[key].avg.products[prodKey] for prodkey in self.replicateExperimentObjectDict[key] for key in strainsToPlot if getattr(self.replicateExperimentObjectDict[key].runIdentifier,sortBy) == unique]) > maxSamples:
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
        for singleExperiment in self.replicateExperimentObjectDict[strainToPlot[0]].singleExperimentList:
            plt.plot(singleExperiment.OD.timeVec,singleExperiment.OD.dataVec)
        plt.ylabel(singleExperiment.runIdentifier.returnUniqueID())
        # plt.tight_layout()

class runIdentifier(object):
    #Base runIdentifier object
    def __init__(self):
        self.strainID = ''          # e.g. MG1655 dlacI
        self.identifier1 = ''       # e.g. pTOG009
        self.identifier2 = ''       # e.g. IPTG
        self.replicate = None       # e.g. 1
        self.time = None            # e.g. 0
        self.titerName = 'None'     # e.g. Lactate
        self.titerType = 'None'     # e.g. titer or OD

    def getRunIdentifier(self, row):
        if type("asdf") == type(row):
            tempParsedIdentifier = row.split(',')
            #print(tempParsedIdentifier)
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

class timePoint(object):
    def __init__(self, runID, titerName, t, titer):
        self.runIdentifier = runID
        self.titerName = titerName
        self. t = t
        self.titer = titer

    def getUniqueTimePointID(self):
        return self.runIdentifier.strainID+self.runIdentifier.identifier1+self.runIdentifier.identifier2+str(self.runIdentifier.replicate)+self.runIdentifier.titerName

class titerObject():
    def __init__(self):
        self.timePointList = []
        self.runIdentifier = runIdentifier()

    def addTimePoint(self, timePoint):
        raise(Exception("No addTimePoint method defiend in the child"))

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
            raise Exception("No unique ID or time points in titerObject()")

    def getReplicateID(self):
        #return self.runIdentifier
        return self.runIdentifier.strainID+self.runIdentifier.identifier1+self.runIdentifier.identifier2

class timeCourseObject(titerObject):
    def __init__(self):
        titerObject.__init__(self)
        self.timeVec = None
        self._dataVec = None
        self.rate = None
        self.removeDeathPhaseFlag = False
        self.useFilteredDataFlag = False

        self.savgolFilterWindowSize = 51

    @property
    def dataVec(self):
        if self.useFilteredDataFlag == True:
            return savgol_filter(self._dataVec,self.savgolFilterWindowSize,3)
        else:
            return self._dataVec

    @dataVec.setter
    def dataVec(self, dataVec):

        if 1 == 0:
            # Find the last point of the growth phase

            # Find the maximum of the data
            maxGrowthIndex = np.where(dataVec == np.max(dataVec))[0]
            print(maxGrowthIndex)
            # Check points after this for a decrease
            filteredData = savgol_filter(dataVec,51,3)
            diff = np.diff(filteredData)
            count = 1
            flag = 0
            deathPhaseStartIndex = len(dataVec)
            for i in range(maxGrowthIndex,len(dataVec)):
                if diff[i-1] < 0:
                    count += 1
                    flag = 1
                else:
                    if flag == 1:
                        count = 0
                if count > 5:
                    deathPhaseStartIndex = i
                    break

            print('death phase starts at:',deathPhaseStartIndex)




        if self.removeDeathPhaseFlag == True:
            try:
                if np.max(dataVec) > 0.2:
                    filteredData = savgol_filter(dataVec,51,3)
                    diff = np.diff(filteredData)

                    count=0
                    # print(diff)
                    flag = 0
                    for i in range(len(diff)-1):
                        if diff[i] < 0:
                            flag = 1
                            count+=1
                            if count > 20:
                                self._dataVec = filteredData[0:i]
                                self.timeVec = self.timeVec[0:i]
                                break
                        elif count > 0:
                            count = 1
                            flag = 0
                    if flag == 0:
                        self._dataVec = dataVec
                    plt.plot(self._dataVec,'r.')
                    plt.plot(dataVec,'b-')
                    plt.show()
                else:
                   self._dataVec = dataVec

                if len(self.dataVec)>6:
                    self.calcExponentialRate()
            except:
                self._dataVec = filteredData#dataVec

                if len(self.dataVec)>6:
                    self.calcExponentialRate()
        else:
            self._dataVec = dataVec

            if len(self.dataVec)>6:
                self.calcExponentialRate()

    # def returnCurveFitPoints(self, t):
    #    # print(self.rate)
    #    Linf = self.rate[0]
    #    k = self.rate[1]
    #    delta = self.rate[2]
    #    gamma = self.rate[3]
    #
    #    return Linf*np.power((1+(delta-1)*np.exp(-k*(t-gamma))) ,1/(1-delta))


    # Generalized Logistic Return Curve Fit
    def returnCurveFitPoints(self, t):
       # print(self.rate)
       A = self.rate[0]
       B = self.rate[1]
       C = self.rate[2]
       Q = self.rate[3]
       K = self.rate[4]
       nu = self.rate[5]
       return A + (    (K-A)      /     (     np.power((C+Q*np.exp(-B*t)),(1/nu))     )       )

    # def returnCurveFitPoints(self, t):
    #
    #     # Gompertz 3 param
    #     # # print(self.rate)
    #     # A = self.rate[0]
    #     # mu = self.rate[1]
    #     # lamb = self.rate[2]
    #     # return A*np.exp(-np.exp(mu*np.e/A*(lamb-t)+1))
    #
    #     # Richard 4 param
    #     A = self.rate[0]
    #     mu = self.rate[1]
    #     lamb = self.rate[2]
    #     nu = self.rate[3]
    #     return A*np.power((1+nu*np.exp(1+nu)*np.exp(mu/A*np.power((1+nu),(1+1/nu))*(lamb-t))),(-1/nu))

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
        #Define the growth equation to fit parameters

        # # 4-parameter Richard Equation
        # def growthEquation(t, Linf, k, gamma, delta):#, K, Q, nu):
        #     return Linf*np.power((1+(delta-1)*np.exp(-k*(t-gamma))) ,1/(1-delta))



        # # Gompertz 3 param
        # def growthEquation(t, A, mu, lamb):
        #     return A*np.exp(-np.exp(mu*np.e/A*(lamb-t)+1))

        # # Modified Richards 4 param
        # def growthEquation(t, A, mu, lamb, nu):
        #     return A*np.power((1+nu*np.exp(1+nu)*np.exp(mu/A*np.power((1+nu),(1+1/nu))*(lamb-t))),(-1/nu))

        # Generalized logistic
        def growthEquation(t, A, B, C, K, Q, nu):
            # return A * B / (A+((B-A)*np.exp(-C*t)))
            return A + ((K-A)/(np.power((C+Q*np.exp(-B*t)),(1/nu))))

        # Fit and return the parameters
        gmod = Model(growthEquation)

        if self.runIdentifier.titerType == 'titer' or self.runIdentifier.titerType == 'substrate' or self.runIdentifier.titerType == 'product':
            gmod.set_param_hint('A', value=np.min(self.dataVec))
            gmod.set_param_hint('B',value=2)
            gmod.set_param_hint('C', value=1, vary=False)
            gmod.set_param_hint('Q', value=0.1)#, max = 10)
            gmod.set_param_hint('K', value = max(self.dataVec))#, max=5)
            gmod.set_param_hint('nu', value=1, vary=False)
        elif self.runIdentifier.titerType == 'OD':
            # gmod.set_param_hint('Linf', value=0.1, max=1)#np.min(self.dataVec), min=0.9*np.min(self.dataVec),max=1.1*np.min(self.dataVec))
            # gmod.set_param_hint('k',value=.25)#, min=0.001, max=0.5)
            # gmod.set_param_hint('delta', value=0)#, vary=False)#, vary=False)#, min=0.99, max=1.01)#, vary=False)
            # gmod.set_param_hint('gamma', value=0)#, min = 1, max = 10)#value=8)#, max = 10)

            #Generalized Logistic Parameters
            gmod.set_param_hint('A', value=np.min(self.dataVec), min=0.9*np.min(self.dataVec),max=1.1*np.min(self.dataVec))
            gmod.set_param_hint('B',value=0.5, min=0.001, max=1)
            gmod.set_param_hint('C', value=1)#, vary=False)#, min = 0.7)#, vary=False)#, vary=False)#, min=0.99, max=1.01)#, vary=False)
            gmod.set_param_hint('Q', value=0.01)#, min = 1, max = 10)#value=8)#, max = 10)
            gmod.set_param_hint('K', value = max(self.dataVec), max=1.1*max(self.dataVec))
            gmod.set_param_hint('nu', value=1)#, vary=False)

            # # Gompertz Parameters
            # gmod.set_param_hint('A', value=np.min(self.dataVec))
            # gmod.set_param_hint('mu',value=0.5)#, min=0.001, max=0.5)
            # gmod.set_param_hint('lamb', value=1)#, vary=False)#, min = 0.7)#, vary=False)#, vary=False)#, min=0.99, max=1.01)#, vary=False)

            # # Richard Parameters
            # gmod.set_param_hint('A', value=np.max(self.dataVec), max=np.max(self.dataVec))
            # gmod.set_param_hint('mu',value=0.01, min=0.001, max=0.5)#, min=0.001, max=0.5)
            # gmod.set_param_hint('lamb', value=-6)#)np.log(0.15))#, min=-1)# min=np.log(np.min(self.dataVec)*0.9))#, vary=False)#, min = 0.7)#, vary=False)#, vary=False)#, min=0.99, max=1.01)#, vary=False)
            # gmod.set_param_hint('nu',value=1)#, min=-5, max=5)

        else:
            print('Unidentified titer type:'+self.runIdentifier.titerType)
        params = gmod.make_params()

        result = gmod.fit (self.dataVec, params, t=self.timeVec, method = 'slsqp')

        # print(result.best_values)
        # plt.plot(self.timeVec,self.dataVec, 'bo')
        # plt.plot(self.timeVec,  result.init_fit,'k--')
        # plt.plot(self.timeVec, result.best_fit,'r-')
        # plt.show()

        self.rate = [0,0,0,0,0,0]
        # # 4-Parameter Richard
        # for key in result.best_values:
        #     if key == 'Linf':
        #         self.rate[0] = result.best_values[key]
        #     if key == 'k':
        #         self.rate[1] = result.best_values[key]
        #     if key == 'delta':
        #         self.rate[2] = result.best_values[key]
        #     if key == 'gamma':
        #         self.rate[3] = result.best_values[key]

        # Generalized Logistic params
        for key in result.best_values:
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

        # # Gompertz
        # for key in result.best_values:
        #     if key == 'A':
        #         self.rate[0] = result.best_values[key]
        #     if key == 'mu':
        #         self.rate[1] = result.best_values[key]
        #     if key == 'lamb':
        #         self.rate[2] = result.best_values[key]

        # # Richard
        # for key in result.best_values:
        #     if key == 'A':
        #         self.rate[0] = result.best_values[key]
        #     if key == 'mu':
        #         self.rate[1] = result.best_values[key]
        #     if key == 'lamb':
        #         self.rate[2] = result.best_values[key]
        #     if key == 'nu':
        #         self.rate[3] = result.best_values[key]

        # if len(self.dataVec)>10:
        #     print(result.best_values)
        #     print(self.rate)

            # plt.plot(self.timeVec,y, 'bo')
            # #plt.plot(self.timeVec,  result.init_fit,'k--')
            # #plt.plot(self.timeVec, result.best_fit,'r-')
            # plt.plot(self.timeVec,self.returnCurveFitPoints(self.timeVec),'g-')
            # print(self.returnCurveFitPoints(self.timeVec))
            # plt.show()

class timeCourseObjectShell(timeCourseObject):
    @timeCourseObject.dataVec.setter
    def dataVec(self, dataVec):
        self._dataVec = dataVec

class endPointObject(titerObject):
    def __init__(self, runID, t, data):
        titerObject.__init__(self, runID, t, data)

    def addTimePoint(self, timePoint):
        if len(self.timePointList) < 2:
            self.timePointList.append(timePoint)
        else:
            raise Exception("Cannot have more than two timePoints for an endPoint Object")

        if len(self.timePointList) == 2:
            self.timePointList.sort(key=lambda timePoint: timePoint.t)

class singleExperimentData(object):
    #Object contains a series of timeCourseObjects related to a single experiment
    def __init__(self):
        self._t = np.array([])
        self.titerObjectList = dict()

        self.ODKey = None
        self.productKeys = []
        self.substrateKey = None
        self.fluorescenceKeys = None

        self.runIdentifier = runIdentifier()

        self._OD = None
        self._substrate = None
        self._products = dict()
        self._fluorescence = dict()

        self.yields = dict()

    # --------------------------- Setters and Getters
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

class singleExperimentDataShell(singleExperimentData):
    def __init__(self):
        singleExperimentData.__init__(self)
        #self._OD = timeCourseObjectShell()

    @singleExperimentData.substrate.setter
    def substrate(self, substrate):
        self._substrate = substrate

    @singleExperimentData.OD.setter
    def OD(self, OD):
        self._OD = OD

    @singleExperimentData.products.setter
    def products(self, products):
        self._products = products

class replicateExperimentObject(object):
    #Calculates statistics based on replicates
    def __init__(self):
        self.avg = singleExperimentDataShell()
        self.std = singleExperimentDataShell()
        self.t = None
        self.singleExperimentList = []
        self.runIdentifier = runIdentifier()
        self.useReplicate = dict()
        self.badReplicates = []
        self.replicateIDs = []
        #self.checkReplicateUniqueIDMatch()


    def checkReplicateUniqueIDMatch(self):
        for i in range(len(self.singleExperimentList)-1):
            if self.singleExperimentList[i].getUniqueReplicateID() != self.singleExperimentList[i+1].getUniqueReplicateID():
                raise Exception("the replicates do not have the same uniqueID, either the uniqueID includes too much information or the strains don't match")

            if (self.singleExperimentList[i].t != self.singleExperimentList[i+1].t).all():
                print(self.singleExperimentList[i].t,self.singleExperimentList[i].t)
                raise Exception("time vectors don't match within replicates")
            else:
                self.t = self.singleExperimentList[i].t

            if len(self.singleExperimentList[i].t) != len(self.singleExperimentList[i+1].t): #TODO
                print("Time Vector 1: ",self.singleExperimentList[i].t,"\nTime Vector 2: ",self.singleExperimentList[i+1].t)
                print("Vector 1: ",self.singleExperimentList[i].substrate.dataVec,"\nVector 2: ",self.singleExperimentList[i+1].substrate.dataVec)
                raise(Exception("length of substrate vectors do not match"))

            for key in self.singleExperimentList[i].products:
                if len(self.singleExperimentList[i].products[key].dataVec) != len(self.singleExperimentList[i+1].products[key].dataVec):
                    raise(Exception("length of product vector "+str(key)+" do not match"))

    def addReplicateExperiment(self, newReplicateExperiment):
        self.singleExperimentList.append(newReplicateExperiment)
        if len(self.singleExperimentList)==1:
            self.t = self.singleExperimentList[0].t
        self.checkReplicateUniqueIDMatch()

        self.runIdentifier = newReplicateExperiment.runIdentifier
        # self.runIdentifier.replicate = None
        self.runIdentifier.time = None
        # print('Replicate being added: ',newReplicateExperiment.runIdentifier.replicate)
        self.replicateIDs.append(newReplicateExperiment.runIdentifier.replicate)
        self.replicateIDs.sort()
        # print('number of replicates: ',len(self.replicateIDs))
        self.calcAverageAndDev()
        # print('Replicate IDs: ',self.replicateIDs)
        # for i in self.replicateIDs:
        #     print(i)

    def calcAverageAndDev(self):    #Calculate averages
        #First check what data exists
        ODflag = 0
        productFlag = 0
        substrateFlag = 0
        yieldFlag = 0
        for singleExperiment in self.singleExperimentList:
            if singleExperiment.OD:
                ODflag = 1
            if singleExperiment.products:
                productFlag = 1 #TODO need to make generic for different products in different expts
            if singleExperiment.substrate:
                substrateFlag=1
            if singleExperiment.yields:
                yieldFlag = 1

        if ODflag == 1:
            self.avg.OD = timeCourseObjectShell()
            self.std.OD = timeCourseObjectShell()
            self.avg.OD.timeVec = self.t
            # Perform outlier test
            # print('Number of Replicates: ',len(self.replicateIDs))
            self.badReplicates = []
            if len(self.replicateIDs) > 2:
                tempVar = 0
                tempRate = dict()
                for testReplicate in self.replicateIDs:
                    tempRate[testReplicate] = np.std([singleExperimentObject.OD.rate for singleExperimentObject in self.singleExperimentList
                                                      if singleExperimentObject.runIdentifier.replicate != testReplicate], axis=0)[1]   # Perform this test only on growth rate
                    # print('repnum',testReplicate,'STDEV',tempRate[testReplicate])
                # minDev = 9999
                # minDevKey = ''
                # for tempRateKey in tempRate:
                #     if tempRate[tempRateKey] < minDev:
                #         minDevKey = tempRateKey
                minDevKey = min(tempRate,key=tempRate.get)
                # for tempRateKey in tempRate:
                tempRateKey = minDevKey
                # print(tempRate[tempRateKey])
                # print(np.mean([tempRate[tempRateKey2] for tempRateKey2 in tempRate if tempRateKey2 != tempRateKey]))
                # print(tempRate[tempRateKey]/np.mean([tempRate[tempRateKey2] for tempRateKey2 in tempRate if tempRateKey2 != tempRateKey]))
                # print(np.abs(tempRate[tempRateKey]-np.mean([tempRate[tempRateKey2] for tempRateKey2 in tempRate if tempRateKey2 != tempRateKey]))/np.mean([tempRate[tempRateKey2] for tempRateKey2 in tempRate if tempRateKey2 != tempRateKey]))
                if tempRate[tempRateKey]/np.mean([tempRate[tempRateKey2] for tempRateKey2 in tempRate if tempRateKey2 != tempRateKey]) < 0.5 :
                    self.badReplicates.append(int(tempRateKey))

            # print(self.badReplicates)
            self.avg.OD.dataVec = np.mean([singleExperimentObject.OD.dataVec for singleExperimentObject in self.singleExperimentList if singleExperimentObject.runIdentifier.replicate not in self.badReplicates], axis=0)
            self.std.OD.dataVec = np.std([singleExperimentObject.OD.dataVec for singleExperimentObject in self.singleExperimentList if singleExperimentObject.runIdentifier.replicate not in self.badReplicates], axis=0)
            self.avg.OD.rate = np.mean([singleExperimentObject.OD.rate for singleExperimentObject in self.singleExperimentList if singleExperimentObject.runIdentifier.replicate not in self.badReplicates], axis=0)#calcExponentialRate()
            self.std.OD.rate = np.std([singleExperimentObject.OD.rate for singleExperimentObject in self.singleExperimentList if singleExperimentObject.runIdentifier.replicate not in self.badReplicates], axis=0)

        if productFlag == 1:
            for key in self.singleExperimentList[0].products:
                self.avg.products[key] = timeCourseObjectShell()
                self.std.products[key] = timeCourseObjectShell()
                self.avg.products[key].dataVec = np.mean([singleExperimentObject.products[key].dataVec for singleExperimentObject in self.singleExperimentList],axis=0)
                self.std.products[key].dataVec = np.std([singleExperimentObject.products[key].dataVec for singleExperimentObject in self.singleExperimentList],axis=0)
                self.avg.products[key].rate = np.mean([singleExperimentObject.products[key].rate for singleExperimentObject in self.singleExperimentList],axis=0)

        if substrateFlag == 1:
            self.avg.substrate = np.mean([singleExperimentObject.substrate.dataVec for singleExperimentObject in self.singleExperimentList], axis=0)
            self.std.substrate = np.std([singleExperimentObject.substrate.dataVec for singleExperimentObject in self.singleExperimentList], axis=0)

        if yieldFlag == 1:
            for key in self.singleExperimentList[0].yields:
                self.avg.yields[key] = np.mean([singleExperimentObject.yields[key] for singleExperimentObject in self.singleExperimentList],axis=0)
                self.std.yields[key] = np.std([singleExperimentObject.yields[key] for singleExperimentObject in self.singleExperimentList],axis=0)