from .TimePoint import *
from .Titer import *
from .TrialIdentifier import *
from .SingleTrial import *
from .ReplicateTrial import *

import sqlite3 as sql

import time
import copy
from pyexcel_xlsx import get_data
import matplotlib.pyplot as plt

class Experiment(object):
    colorMap = 'Set2'

    def __init__(self, info=None):
        # Initialize variables
        self.timePointList = []  # dict()
        self.titerObjectDict = dict()
        self.singleExperimentObjectDict = dict()
        self.replicateExperimentObjectDict = dict()
        self.infoKeys = ['importDate', 'runStartDate', 'runEndDate', 'experimentTitle', 'principalScientistName',
                         'secondaryScientistName', 'mediumBase', 'mediumSupplements', 'notes']
        if info != None:
            self.info = {key: info[key] for key in self.infoKeys if key in info}
        else:
            self.info = dict()

    def commitToDB(self, dbName):
        conn = sql.connect(dbName)
        c = conn.cursor()
        preppedCols = list(self.info.keys())
        preppedColQuery = ', '.join(col for col in preppedCols)
        preppedColData = [self.info[key] for key in preppedCols]
        c.execute("""\
           INSERT INTO experimentTable
           (""" + preppedColQuery + """) VALUES (""" + ', '.join('?' for a in preppedColData) + """)""", preppedColData)
        c.execute("SELECT MAX(experimentID) FROM experimentTable")
        experimentID = c.fetchall()[0][0]
        for key in self.replicateExperimentObjectDict:
            self.replicateExperimentObjectDict[key].commitToDB(experimentID, c=c)

        conn.commit()
        c.close()

        print('Committed experiment #', experimentID, ' to DB ', dbName)
        return experimentID

    def loadFromDB(self, dbName, experimentID):
        conn = sql.connect(dbName)
        c = conn.cursor()
        c.execute("""SELECT * FROM experimentTable WHERE (experimentID == ?)""", (experimentID,))
        self.exptDescription = {key: data for data, key in zip(c.fetchall()[0], [elem[0] for elem in c.description])}

        # Build the replicate experiment objects
        c.execute("""SELECT  strainID, identifier1, identifier2, identifier3, replicateID FROM replicateTable
                WHERE experimentID == ?""", (experimentID,))
        for row in c.fetchall():
            self.replicateExperimentObjectDict[row[0] + row[1] + row[2]] = ReplicateTrial()
            self.replicateExperimentObjectDict[row[0] + row[1] + row[2]].runIdentifier.strainID = row[0]
            self.replicateExperimentObjectDict[row[0] + row[1] + row[2]].runIdentifier.identifier1 = row[1]
            self.replicateExperimentObjectDict[row[0] + row[1] + row[2]].runIdentifier.identifier2 = row[2]
            self.replicateExperimentObjectDict[row[0] + row[1] + row[2]].runIdentifier.identifier3 = row[3]
            self.replicateExperimentObjectDict[row[0] + row[1] + row[2]].loadFromDB(c=c, replicateID=row[4])

    def getAllStrains_django(self, dbName, experimentID):
        """
        :param dbName:
        :param experimentID:
        :return:
        """
        conn = sql.connect(dbName)
        c = conn.cursor()
        c.execute("""SELECT * FROM experimentTable WHERE (experimentID == ?)""", (experimentID,))
        exptDescription = {key: data for data, key in zip(c.fetchall()[0], [elem[0] for elem in c.description])}

        # Build the replicate experiment objects
        c.execute("""SELECT  strainID, identifier1, identifier2, identifier3, replicateID, experimentID FROM replicateTable
                WHERE experimentID == ? ORDER BY strainID DESC, identifier1 DESC, identifier2 DESC""", (experimentID,))
        strainDescriptions = []
        for row in c.fetchall():
            strainDescriptions.append({key: data for data, key in zip(row, [elem[0] for elem in c.description])})
        c.close()
        return strainDescriptions

    def plottingGUI(self):
        app = QtGui.QApplication(sys.argv)

        main = Window(self)
        main.showMaximized()

        sys.exit(app.exec_())

    def getAllStrains(self):
        temp = [key for key in self.replicateExperimentObjectDict if
                self.replicateExperimentObjectDict[key].runIdentifier.identifier1 != '']
        temp.sort()
        return temp

    def getAllTiters(self):
        titersToPlot = [[[titer for titer in singleExperiment.titerObjectDict] for singleExperiment in
                         self.replicateExperimentObjectDict[key].singleTrialList] for key in
                        self.replicateExperimentObjectDict]

        # Flatten list and find the uniques
        titersToPlot = [y for x in titersToPlot for y in x]
        titersToPlot = list(set([y for x in titersToPlot for y in x]))

        return titersToPlot

    def parseRawData(self, dataFormat, fileName=None, data=None):
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
                if type(row[0]) is str:
                    temp_run_identifier_object.parse_RunIdentifier_from_csv(row[0])
                    temp_run_identifier_object.titerName = 'OD600'
                    temp_run_identifier_object.titerType = 'biomass'
                    tempTimeCourseObject = TimeCourse()
                    tempTimeCourseObject.runIdentifier = temp_run_identifier_object
                    # Data in seconds, data required to be in hours
                    # print(data[0][1:])
                    tempTimeCourseObject.timeVec = np.array(np.divide(data[0][1:], 3600))

                    tempTimeCourseObject.dataVec = np.array(row[1:])
                    self.titerObjectDict[tempTimeCourseObject.getTimeCourseID()] = copy.copy(tempTimeCourseObject)

            tf = time.time()
            print("Parsed %i timeCourseObjects in %0.3fs\n" % (len(self.titerObjectDict), tf - t0))

            self.parseTiterObjectCollection(self.titerObjectDict)

        if dataFormat == 'NV_titers':
            substrateName = 'Glucose'
            titerDataSheetName = "titers"

            if 'titers' not in data.keys():
                raise Exception("No sheet named 'titers' found")

            ######## Initialize variables
            titerNameColumn = dict()
            for i in range(1, len(data[titerDataSheetName][2])):
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
                if type("asdf") == type(data['titers'][i][0]):  # Check if the data is a string
                    tempParsedIdentifier = data['titers'][i][0].split(',')  # Parse the string using comma delimiter
                    if len(tempParsedIdentifier) >= 3:  # Ensure corect number of identifiers TODO make this general
                        tempRunIdentifierObject = RunIdentifier()
                        tempParsedStrainIdentifier = tempParsedIdentifier[0].split("+")
                        tempRunIdentifierObject.strainID = tempParsedStrainIdentifier[0]
                        tempRunIdentifierObject.identifier1 = tempParsedStrainIdentifier[1]
                        # tempRunIdentifierObject.identifier2 = tempParsedIdentifier[2]
                        tempParsedReplicate = tempParsedIdentifier[1].split('=')
                        tempRunIdentifierObject.replicate = int(tempParsedReplicate[1])  # tempParsedIdentifier[1]
                        tempParsedTime = tempParsedIdentifier[2].split('=')
                        tempRunIdentifierObject.t = float(tempParsedTime[1])  # tempParsedIdentifier[2]

                        for key in tempTimePointCollection:
                            tempRunIdentifierObject.titerName = key
                            if key == 'Glucose':
                                tempRunIdentifierObject.titerType = 'substrate'
                            else:
                                tempRunIdentifierObject.titerType = 'product'
                            self.timePointList.append(
                                TimePoint(copy.copy(tempRunIdentifierObject), key, tempRunIdentifierObject.t,
                                          data['titers'][i][titerNameColumn[key]]))

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
            for i in range(1, len(data[titerDataSheetName][2])):
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
                if type("asdf") == type(data['titers'][i][0]):  # Check if the data is a string
                    temp_run_identifier_object = RunIdentifier()
                    temp_run_identifier_object.parse_RunIdentifier_from_csv(data['titers'][i][0])

                    tempParsedIdentifier = data['titers'][i][0].split(',')  # Parse the string using comma delimiter

                    temp_run_identifier_object.t = 15.  # tempParsedIdentifier[2]

                    for key in tempTimePointCollection:
                        temp_run_identifier_object.titerName = key
                        if key == 'Glucose':
                            temp_run_identifier_object.titerType = 'substrate'
                            self.timePointList.append(TimePoint(copy.copy(temp_run_identifier_object), key, 0, 12))
                        else:
                            temp_run_identifier_object.titerType = 'product'
                            self.timePointList.append(TimePoint(copy.copy(temp_run_identifier_object), key, 0, 0))
                        self.timePointList.append(
                            TimePoint(copy.copy(temp_run_identifier_object), key, temp_run_identifier_object.t,
                                      data['titers'][i][titerNameColumn[key]]))


                    else:
                        skippedLines += 1
                else:
                    skippedLines += 1

            tf = time.time()
            print("Parsed %i timeCourseObjects in %0.3fs\n" % (len(self.timePointList), tf - t0))
            print("Number of lines skipped: ", skippedLines)
            self.parseTimePointCollection(self.timePointList)

        if dataFormat == 'KN_titers':
            # Parameters
            row_with_titer_names = 0
            first_data_row = 1

            substrateName = 'Glucose'
            titerDataSheetName = "titers"

            if 'titers' not in data.keys():
                raise Exception("No sheet named 'titers' found")

            # Initialize variables
            titerNameColumn = dict()
            for i in range(1, len(data[titerDataSheetName][row_with_titer_names])):
                titerNameColumn[data[titerDataSheetName][2][i]] = i

            tempTimePointCollection = dict()
            for names in titerNameColumn:
                tempTimePointCollection[names] = []

            timePointCollection = []
            skippedLines = 0


            for i in range(first_data_row, len(data['titers'])):
                if type(data['titers'][i][0]) is str:
                    temp_run_identifier_object = RunIdentifier()
                    temp_run_identifier_object.parse_RunIdentifier_from_csv(data['titers'][i][0])

                    for key in tempTimePointCollection:
                        temp_run_identifier_object.titerName = key

                        self.timePointList.append(
                            TimePoint(copy.copy(temp_run_identifier_object), key, temp_run_identifier_object.t,
                                      data['titers'][i][titerNameColumn[key]]))
                    else:
                        skippedLines += 1
                else:
                    skippedLines += 1

            tf = time.time()
            print("Parsed %i timeCourseObjects in %0.3fs\n" % (len(self.timePointList), tf - t0))
            print("Number of lines skipped: ", skippedLines)
            self.parseTimePointCollection(self.timePointList)

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
        print("Parsed %i titer objects in %0.1fs\n" % (len(self.titerObjectDict), (tf - t0)))
        self.parseTiterObjectCollection(self.titerObjectDict)

    def parseTiterObjectCollection(self, titerObjectDict):
        print('Parsing titer object list...')
        t0 = time.time()
        for titerObjectDictKey in titerObjectDict:
            if titerObjectDict[titerObjectDictKey].getTimeCourseID() in self.singleExperimentObjectDict:
                self.singleExperimentObjectDict[titerObjectDict[titerObjectDictKey].getTimeCourseID()].addTiterObject(
                    titerObjectDict[titerObjectDictKey])
            else:
                self.singleExperimentObjectDict[titerObjectDict[titerObjectDictKey].getTimeCourseID()] = SingleTrial()
                self.singleExperimentObjectDict[titerObjectDict[titerObjectDictKey].getTimeCourseID()].addTiterObject(
                    titerObjectDict[titerObjectDictKey])
        tf = time.time()
        print("Parsed %i titer objects in %0.1fms\n" % (len(self.singleExperimentObjectDict), (tf - t0) * 1000))
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
                self.replicateExperimentObjectDict[
                    singleExperimentObjectList[key].getUniqueReplicateID()] = ReplicateTrial()
                self.replicateExperimentObjectDict[
                    singleExperimentObjectList[key].getUniqueReplicateID()].addReplicateExperiment(
                    singleExperimentObjectList[key])
        tf = time.time()
        print("Parsed %i titer objects in %0.1fs\n" % (len(self.replicateExperimentObjectDict), (tf - t0)))

    def addReplicateTrial(self, replicateTrial):
        self.replicateExperimentObjectDict[replicateTrial.singleTrialList[0].getUniqueReplicateID()] = replicateTrial

    def pickle(self, fileName):
        pickle.dump([self.timePointList, self.titerObjectDict, self.singleExperimentObjectDict,
                     self.replicateExperimentObjectDict], open(fileName, 'wb'))

    def unpickle(self, fileName):
        t0 = time.time()
        with open(fileName, 'rb') as data:
            self.timePointList, self.titerObjectDict, self.singleExperimentObjectDict, self.replicateExperimentObjectDict = pickle.load(
                data)
        print('Read data from %s in %0.3fs' % (fileName, time.time() - t0))

    def printGenericTimeCourse(self, figHandle=[], strainsToPlot=[], titersToPlot=[], removePointFraction=1,
                               shadeErrorRegion=False, showGrowthRates=True, plotCurveFit=True, output_type='iPython'):

        if strainsToPlot == []:
            strainsToPlot = self.getAllStrains()
        # Plot all product titers if none specified TODO: Add an option to plot OD as well
        if titersToPlot == []:
            titersToPlot = self.getAllTiters()

        replicateTrialList = [self.replicateExperimentObjectDict[key] for key in strainsToPlot]

        from FermAT import printGenericTimeCourse_plotly
        printGenericTimeCourse_plotly(replicateTrialList=replicateTrialList, titersToPlot=titersToPlot,
                                      output_type=output_type)



        # if figHandle == []:
        #     figHandle = plt.figure(figsize=(12, 8))
        #
        # figHandle.set_facecolor('w')
        #

        #
        # # Determine optimal figure size
        # if len(titersToPlot) == 1:
        #     figureSize = (12, 6)
        # if len(titersToPlot) > 1:
        #     figureSize = (12, 3.5)
        # if len(titersToPlot) > 4:
        #     figureSize = (12, 7)
        #
        # if plotCurveFit == True:
        #     plotSymbol = 'o'
        # else:
        #     plotSymbol = 'o-'
        #
        # figHandle  # .set_size_inches(figureSize, forward=True)
        # # plt.figure(figsize=figureSize)
        # plt.clf()
        #
        # colors = plt.get_cmap(self.colorMap)(np.linspace(0, 1, len(strainsToPlot)))
        #
        # pltNum = 0
        # print(titersToPlot)
        # for product in titersToPlot:
        #     pltNum += 1
        #
        #     # Choose the subplot layout
        #     if len(titersToPlot) == 1:
        #         ax = plt.subplot(111)
        #     elif len(titersToPlot) < 5:
        #         ax = plt.subplot(1, len(titersToPlot), pltNum)
        #     elif len(titersToPlot) < 9:
        #         ax = plt.subplot(2, (len(titersToPlot) + 1) / 2, pltNum)
        #     else:
        #         raise Exception("Unimplemented Functionality")
        #
        #     # Set some axis aesthetics
        #     ax.spines["top"].set_visible(False)
        #     ax.spines["right"].set_visible(False)
        #
        #     colorIndex = 0
        #     handle = dict()
        #     xlabel = 'Time (hours)'
        #     for key in strainsToPlot:
        #         xData = self.replicateExperimentObjectDict[key].t
        #         if product == 'OD' or product == self.replicateExperimentObjectDict[key].avg.titerObjectDict[product].runIdentifier.titerName:
        #             product = self.replicateExperimentObjectDict[key].avg.titerObjectDict[product].runIdentifier.titerName
        #             scaledTime = self.replicateExperimentObjectDict[key].t
        #             # Plot the fit curve
        #             if plotCurveFit == True:
        #                 handle[key] = plt.plot(np.linspace(min(scaledTime), max(scaledTime), 50),
        #                                        self.replicateExperimentObjectDict[key].avg.titerObjectDict[
        #                                            product].returnCurveFitPoints(
        #                                            np.linspace(min(self.replicateExperimentObjectDict[key].t),
        #                                                        max(self.replicateExperimentObjectDict[key].t), 50)),
        #                                        '-', lw=1.5, color=colors[colorIndex])
        #             # Plot the data
        #             print(product)
        #             print(scaledTime[::removePointFraction])
        #             print()
        #             handle[key] = plt.errorbar(scaledTime[::removePointFraction],
        #                                        self.replicateExperimentObjectDict[key].avg.titerObjectDict[
        #                                            product].dataVec[::removePointFraction],
        #                                        self.replicateExperimentObjectDict[key].std.titerObjectDict[
        #                                            product].dataVec[::removePointFraction],
        #                                        lw=2.5, elinewidth=1, capsize=2, fmt=plotSymbol, markersize=5,
        #                                        color=colors[colorIndex])
        #             # Fill in the error bar range
        #             # if shadeErrorRegion==True:
        #             #     plt.fill_between(scaledTime,self.replicateExperimentObjectDict[key].avg.OD.dataVec+self.replicateExperimentObjectDict[key].std.OD.dataVec,
        #             #                      self.replicateExperimentObjectDict[key].avg.OD.dataVec-self.replicateExperimentObjectDict[key].std.OD.dataVec,
        #             #                      facecolor=colors[colorIndex],alpha=0.1)
        #             # # Add growth rates at end of curve
        #             # if showGrowthRates==True:
        #             #     plt.text(scaledTime[-1]+0.5,
        #             #              self.replicateExperimentObjectDict[key].avg.OD.returnCurveFitPoints(np.linspace(min(self.replicateExperimentObjectDict[key].t),max(self.replicateExperimentObjectDict[key].t),50))[-1],
        #             #              '$\mu$ = '+'{:.2f}'.format(self.replicateExperimentObjectDict[key].avg.OD.rate[1]) + ' $\pm$ ' + '{:.2f}'.format(self.replicateExperimentObjectDict[key].std.OD.rate[1])+', n='+str(len(self.replicateExperimentObjectDict[key].replicateIDs)-len(self.replicateExperimentObjectDict[key].badReplicates)),
        #             #              verticalalignment='center')
        #             # ylabel = 'OD$_{600}$'
        #         else:
        #             scaledTime = self.replicateExperimentObjectDict[key].t
        #
        #             # handle[key] = plt.plot(np.linspace(min(scaledTime),max(scaledTime),50),
        #             #                         self.replicateExperimentObjectDict[key].avg.products[product].returnCurveFitPoints(np.linspace(min(self.replicateExperimentObjectDict[key].t),max(self.replicateExperimentObjectDict[key].t),50)),
        #             #                        '-',lw=0.5,color=colors[colorIndex])
        #
        #             handle[key] = plt.errorbar(self.replicateExperimentObjectDict[key].t[::removePointFraction],
        #                                        self.replicateExperimentObjectDict[key].avg.titerObjectDict[
        #                                            product].dataVec[::removePointFraction],
        #                                        self.replicateExperimentObjectDict[key].std.titerObjectDict[
        #                                            product].dataVec[::removePointFraction], lw=2.5, elinewidth=1,
        #                                        capsize=2, fmt='o-', color=colors[colorIndex])
        #             ylabel = product + " Titer (g/L)"
        #
        #         colorIndex += 1
        #         # plt.show()
        #     plt.xlabel(xlabel)
        #     # plt.ylabel(ylabel)
        #     ymin, ymax = plt.ylim()
        #     xmin, xmax = plt.xlim()
        #     plt.xlim([0, xmax * 1.2])
        #     plt.ylim([0, ymax])
        # # plt.style.use('ggplot')
        # plt.tight_layout()
        # plt.tick_params(right="off", top="off")
        # # plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0, frameon=False)
        # plt.subplots_adjust(right=0.7)
        #
        # if len(titersToPlot) == 1:
        #     plt.legend([handle[key] for key in handle], [key for key in handle], bbox_to_anchor=(1.05, 0.5), loc=6,
        #                borderaxespad=0, frameon=False)
        #     plt.subplots_adjust(right=0.7)
        # elif len(titersToPlot) < 5:
        #     plt.legend([handle[key] for key in handle], [key for key in handle], bbox_to_anchor=(1.05, 0.5), loc=6,
        #                borderaxespad=0, frameon=False)
        #     plt.subplots_adjust(right=0.75)
        # else:
        #     plt.legend([handle[key] for key in handle], [key for key in handle], bbox_to_anchor=(1.05, 1.1), loc=6,
        #                borderaxespad=0, frameon=False)
        #     plt.subplots_adjust(right=0.75)
        #
        #     # Save the figure
        #     # plt.savefig(os.path.join(os.path.dirname(__file__),'Figures/'+time.strftime('%y')+'.'+time.strftime('%m')+'.'+time.strftime('%d')+" H"+time.strftime('%H')+'-M'+time.strftime('%M')+'-S'+time.strftime('%S')+'.png'))
        #     # plt.show()

    def printGrowthRateBarChart(self, figHandle=[], strainsToPlot=[], sortBy='identifier1'):
        if figHandle == []:
            figHandle = plt.figure(figsize=(9, 5))

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
        uniques = list(
            set([getattr(self.replicateExperimentObjectDict[key].runIdentifier, sortBy) for key in strainsToPlot]))
        uniques.sort()

        # Find max number of samples (in case they all aren't the same)
        maxSamples = 0
        for unique in uniques:
            if len([self.replicateExperimentObjectDict[key].avg.OD.rate[1] for key in strainsToPlot if
                    getattr(self.replicateExperimentObjectDict[key].runIdentifier, sortBy) == unique]) > maxSamples:
                maxSamples = len([self.replicateExperimentObjectDict[key].avg.OD.rate[1] for key in strainsToPlot if
                                  getattr(self.replicateExperimentObjectDict[key].runIdentifier, sortBy) == unique])
                maxIndex = unique

        barWidth = 0.9 / len(uniques)
        index = np.arange(maxSamples)
        colors = plt.get_cmap('Set2')(np.linspace(0, 1.0, len(uniques)))

        i = 0
        handle = dict()
        for unique in uniques:
            handle[unique] = plt.bar(index[0:len(
                [self.replicateExperimentObjectDict[key].avg.OD.rate[1] for key in strainsToPlot if
                 getattr(self.replicateExperimentObjectDict[key].runIdentifier, sortBy) == unique])],
                                     [self.replicateExperimentObjectDict[key].avg.OD.rate[1] for key in strainsToPlot if
                                      getattr(self.replicateExperimentObjectDict[key].runIdentifier, sortBy) == unique],
                                     barWidth, yerr=[self.replicateExperimentObjectDict[key].std.OD.rate[1] for key in
                                                     strainsToPlot if
                                                     getattr(self.replicateExperimentObjectDict[key].runIdentifier,
                                                             sortBy) == unique],
                                     color=colors[i], ecolor='k', capsize=5, error_kw=dict(elinewidth=1, capthick=1))
            i += 1
            index = index + barWidth

        ax.yaxis.set_ticks_position('left')
        ax.xaxis.set_ticks_position('bottom')
        plt.ylabel('Growth Rate ($\mu$, h$^{-1}$)')
        xticklabel = ''
        for attribute in ['strainID', 'identifier1', 'identifier2']:
            if attribute != sortBy:
                xticklabel = xticklabel + attribute

        if 'strainID' == sortBy:
            tempticks = [self.replicateExperimentObjectDict[key].runIdentifier.identifier1 + '+' +
                         self.replicateExperimentObjectDict[key].runIdentifier.identifier2 for key in strainsToPlot
                         if getattr(self.replicateExperimentObjectDict[key].runIdentifier, sortBy) == maxIndex]
        if 'identifier1' == sortBy:
            tempticks = [self.replicateExperimentObjectDict[key].runIdentifier.strainID + '+' +
                         self.replicateExperimentObjectDict[key].runIdentifier.identifier2 for key in strainsToPlot
                         if getattr(self.replicateExperimentObjectDict[key].runIdentifier, sortBy) == maxIndex]
        if 'identifier2' == sortBy:
            tempticks = [self.replicateExperimentObjectDict[key].runIdentifier.strainID + '+' +
                         self.replicateExperimentObjectDict[key].runIdentifier.identifier1 for key in strainsToPlot
                         if getattr(self.replicateExperimentObjectDict[key].runIdentifier, sortBy) == maxIndex]
        tempticks.sort()

        plt.xticks(index - 0.4, tempticks, rotation='45', ha='right', va='top')
        plt.tight_layout()
        plt.subplots_adjust(right=0.75)
        # print([handle[key][0][0] for key in handle])
        plt.legend([handle[key][0] for key in uniques], uniques, bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0)
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
        colors = plt.get_cmap('Set2')(np.linspace(0, 1.0, len(strainsToPlot)))

        barWidth = 0.6
        pltNum = 0

        if withLegend == 2:
            # # First determine which items to separate plot by (titer/OD, strain, id1, id2)
            # # TODO implement this
            #
            # # Then determine which items to group the plot by



            for product in titersToPlot:
                uniques = list(set(
                    [getattr(self.replicateExperimentObjectDict[key].runIdentifier, sortBy) for key in strainsToPlot]))
                uniques.sort()

                # Find max number of samples (in case they all aren't the same)
                maxSamples = 0
                for unique in uniques:
                    if len([self.replicateExperimentObjectDict[key].avg.products[product] for key in strainsToPlot if
                            getattr(self.replicateExperimentObjectDict[key].runIdentifier,
                                    sortBy) == unique]) > maxSamples:
                        # if len([self.replicateExperimentObjectDict[key].avg.products[prodKey] for prodkey in self.replicateExperimentObjectDict[key] for key in strainsToPlot if getattr(self.replicateExperimentObjectDict[key].RunIdentifier,sortBy) == unique]) > maxSamples:
                        maxSamples = len(
                            [self.replicateExperimentObjectDict[key].avg.products[product] for key in strainsToPlot if
                             getattr(self.replicateExperimentObjectDict[key].runIdentifier, sortBy) == unique])
                        maxIndex = unique

                # Create empty arrays to store data
                endPointTiterAvg = []
                endPointTiterStd = []
                endPointTiterLabel = []

                # Choose plot number
                pltNum += 1
                ax = plt.subplot(1, len(titersToPlot), pltNum)

                # Initial variables and choose plotting locations of bars
                location = 0

                # Prepare data for plotting
                for key in strainsToPlot:
                    if getattr(self.replicateExperimentObjectDict[key].runIdentifier, sortBy) == unique:
                        endPointTiterLabel.append(key)
                        endPointTiterAvg.append(replicateExperimentObjectList[key].avg.yields[product][-1])
                        endPointTiterStd.append(replicateExperimentObjectList[key].std.yields[product][-1])

                barWidth = 0.9 / len(uniques)
                index = np.arange(maxSamples)
                colors = plt.get_cmap('Set2')(np.linspace(0, 1.0, len(uniques)))

                i = 0
                for unique in uniques:
                    print([self.replicateExperimentObjectDict[key].avg.yields[product][-1] for key in strainsToPlot if
                           getattr(self.replicateExperimentObjectDict[key].runIdentifier, sortBy) == unique])
                    print(len(
                        [self.replicateExperimentObjectDict[key].avg.yields[product][-1] for key in strainsToPlot if
                         getattr(self.replicateExperimentObjectDict[key].runIdentifier, sortBy) == unique]))
                    print(
                        [getattr(self.replicateExperimentObjectDict[key].runIdentifier, sortBy) for key in strainsToPlot
                         if getattr(self.replicateExperimentObjectDict[key].runIdentifier, sortBy) == unique])
                    print()
                    handle[unique] = plt.bar(index[0:len(
                        [self.replicateExperimentObjectDict[key].avg.products[product] for key in strainsToPlot if
                         getattr(self.replicateExperimentObjectDict[key].runIdentifier, sortBy) == unique])],
                                             [self.replicateExperimentObjectDict[key].avg.yields[product][-1] for key in
                                              strainsToPlot if
                                              getattr(self.replicateExperimentObjectDict[key].runIdentifier,
                                                      sortBy) == unique],
                                             barWidth,
                                             yerr=[self.replicateExperimentObjectDict[key].std.yields[product][-1] for
                                                   key in strainsToPlot if
                                                   getattr(self.replicateExperimentObjectDict[key].runIdentifier,
                                                           sortBy) == unique],
                                             color=colors[i], ecolor='k', capsize=5,
                                             error_kw=dict(elinewidth=1, capthick=1)
                                             )
                    index = index + barWidth
                    i += 1

                plt.ylabel(product + " Yield (g/g)")
                ymin, ymax = plt.ylim()
                plt.ylim([0, ymax])

                endPointTiterLabel.sort()

                xticklabel = ''
                for attribute in ['strainID', 'identifier1', 'identifier2']:
                    if attribute != sortBy:
                        xticklabel = xticklabel + attribute

                if 'strainID' == sortBy:
                    tempticks = [self.replicateExperimentObjectDict[key].runIdentifier.identifier1 + '+' +
                                 self.replicateExperimentObjectDict[key].runIdentifier.identifier2 for key in
                                 strainsToPlot
                                 if getattr(self.replicateExperimentObjectDict[key].runIdentifier, sortBy) == maxIndex]
                if 'identifier1' == sortBy:
                    tempticks = [self.replicateExperimentObjectDict[key].runIdentifier.strainID + '+' +
                                 self.replicateExperimentObjectDict[key].runIdentifier.identifier2 for key in
                                 strainsToPlot
                                 if getattr(self.replicateExperimentObjectDict[key].runIdentifier, sortBy) == maxIndex]
                if 'identifier2' == sortBy:
                    tempticks = [self.replicateExperimentObjectDict[key].runIdentifier.strainID + '+' +
                                 self.replicateExperimentObjectDict[key].runIdentifier.identifier1 for key in
                                 strainsToPlot
                                 if getattr(self.replicateExperimentObjectDict[key].runIdentifier, sortBy) == maxIndex]
                tempticks.sort()

                plt.xticks(index - 0.4, tempticks, rotation='45', ha='right', va='top')

                ax.yaxis.set_ticks_position('left')
                ax.xaxis.set_ticks_position('bottom')
            figManager = plt.get_current_fig_manager()
            figManager.window.showMaximized()
            plt.tight_layout()
            plt.subplots_adjust(right=0.875)
            plt.legend([handle[key][0] for key in uniques], uniques, bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0)

        if withLegend == 0:
            plt.figure(figsize=(6, 3))
            for product in titersToPlot:
                endPointTiterAvg = []
                endPointTiterStd = []
                endPointTiterLabel = []
                pltNum += 1
                # ax = plt.subplot(0.8)
                ax = plt.subplot(1, len(
                    replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products), pltNum)
                ax.spines["top"].set_visible(False)
                # ax.spines["bottom"].set_visible(False)
                ax.spines["right"].set_visible(False)
                # ax.spines["left"].set_visible(False)
                location = 0
                index = np.arange(len(strainsToPlot))

                strainsToPlot.sort()

                for key in strainsToPlot:
                    endPointTiterLabel.append(key)
                    endPointTiterAvg.append(replicateExperimentObjectList[key].avg.yields[product][-1])
                    endPointTiterStd.append(replicateExperimentObjectList[key].std.yields[product][-1])

                handle[key] = plt.bar(index, endPointTiterAvg, barWidth, yerr=endPointTiterStd,
                                      color=plt.get_cmap('Set2')(0.25), ecolor='black', capsize=5,
                                      error_kw=dict(elinewidth=1, capthick=1))
                location += barWidth
                plt.xlabel("Time (hours)")
                plt.ylabel(product + " Yield (g/g)")
                ymin, ymax = plt.ylim()
                plt.ylim([0, ymax])
                plt.tight_layout()
                endPointTiterLabel.sort()
                plt.xticks(index + barWidth / 2, endPointTiterLabel, rotation='45', ha='right', va='top')
                ax.yaxis.set_ticks_position('left')
                ax.xaxis.set_ticks_position('bottom')

        if withLegend == 1:
            plt.figure(figsize=(6, 2))

            for product in replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products:
                endPointTiterAvg = []
                endPointTiterStd = []
                endPointTiterLabel = []
                pltNum += 1
                ax = plt.subplot(1, len(
                    replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products), pltNum)
                ax.spines["top"].set_visible(False)
                # ax.spines["bottom"].set_visible(False)
                ax.spines["right"].set_visible(False)
                # ax.spines["left"].set_visible(False)
                location = 0
                index = np.arange(len(strainsToPlot))

                for key in strainsToPlot:
                    endPointTiterLabel.append(key)
                    endPointTiterAvg.append(replicateExperimentObjectList[key].avg.yields[product][-1])
                    endPointTiterStd.append(replicateExperimentObjectList[key].std.yields[product][-1])

                barList = plt.bar(index, endPointTiterAvg, barWidth, yerr=endPointTiterStd, ecolor='k')
                count = 0
                for bar, count in zip(barList, range(len(strainsToPlot))):
                    bar.set_color(colors[count])
                location += barWidth
                plt.ylabel(product + " Titer (g/L)")
                ymin, ymax = plt.ylim()
                plt.ylim([0, ymax])
                plt.tight_layout()
                plt.xticks([])
                ax.yaxis.set_ticks_position('left')
                ax.xaxis.set_ticks_position('bottom')
            plt.subplots_adjust(right=0.7)
            plt.legend(barList, strainsToPlot, bbox_to_anchor=(1.15, 0.5), loc=6, borderaxespad=0)

    def printYieldTimeCourse(self, strainsToPlot):
        replicateExperimentObjectList = self.replicateExperimentObjectDict
        # You typically want your plot to be ~1.33x wider than tall. This plot is a rare
        # exception because of the number of lines being plotted on it.
        # Common sizes: (10, 7.5) and (12, 9)
        plt.figure(figsize=(12, 3))

        handle = dict()
        barWidth = 0.9 / len(strainsToPlot)
        # plt.hold(False)
        pltNum = 0
        colors = plt.get_cmap('Paired')(np.linspace(0, 1.0, len(strainsToPlot)))
        for product in replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products:
            pltNum += 1
            ax = plt.subplot(1, len(
                replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products) + 1, pltNum)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            location = 0
            colorIndex = 0
            for key in strainsToPlot:
                index = np.arange(len(replicateExperimentObjectList[key].t))
                handle[key] = plt.bar(index + location, replicateExperimentObjectList[key].avg.yields[product],
                                      barWidth, yerr=replicateExperimentObjectList[key].std.yields[product],
                                      color=colors[colorIndex], ecolor='k')
                plt.xticks(index + barWidth, replicateExperimentObjectList[key].t)
                location += barWidth
                colorIndex += 1
                # print(replicateExperimentObjectList[key].avg.products[product].rate)
                # handle[key] = plt.plot(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50),
                #                                    replicateExperimentObjectList[key].avg.products[product].returnCurveFitPoints(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50)),'-',lw=2.5)
            plt.xlabel("Time (hours)")
            plt.ylabel(product + " Yield (g/g)")
            ymin, ymax = plt.ylim()
            plt.ylim([0, 1])
            plt.tight_layout()
        # plt.subplot(1,4,4)
        plt.legend([handle[key] for key in handle], [key for key in handle], bbox_to_anchor=(1.15, 0.5), loc=6,
                   borderaxespad=0)
        plt.subplots_adjust(right=1.05)

    def printAllReplicateTimeCourse(self, figHandle=[], strainToPlot=[]):

        if figHandle == []:
            figHandle = plt.figure(figsize=(9, 5))

        plt.clf()
        if len(strainToPlot) > 1:
            strainToPlot = self.getAllStrains()[0]
        for singleExperiment in self.replicateExperimentObjectDict[strainToPlot[0]].singleTrialList:
            plt.plot(singleExperiment.OD.timeVec, singleExperiment.OD.dataVec)
        plt.ylabel(singleExperiment.runIdentifier.get_unique_id_for_ReplicateTrial())
        # plt.tight_layout()