from fDAPI.TrialIdentifier import RunIdentifier
import sqlite3 as sql

class Project(object):
    """
    """

    colorMap = 'Set3'

    def __init__(self):
        pass
        # self.dbName = 'defaultProjectDatabase.db'
        # try:
        #     print('tried it')
        #     self.experimentList = pickle.load(open('testpickle.p','rb'))
        # except Exception as e:
        #     print('caught it')
        #     self.experimentList = []
        #
        # print('length of experimentList on fileOpen/Create: ',self.experimentList)

        # conn = sql.connect(self.dbName)
        # c = conn.cursor()
        # c.execute("CREATE TABLE IF NOT EXISTS replicateExperiment (experimentID INT, strainID TEXT, identifier1 TEXT, identifier2 TEXT)")
        # c.execute("CREATE TABLE IF NOT EXISTS experiments (dateAdded TEXT, experimentDate TEXT, experimentDescription TEXT)")
        # conn.commit()
        # c.close()
        # conn.close()
        # # print(experimentDataRaw[0])
        # # test = pickle.loads(str(experimentDataRaw[0]))
        # # self.experimentData = [pickle.loads(str(experimentDataRaw[i])) for i in range(len(experimentDataRaw))]
        #
        # # for experiment in self.experimentDataRaw
        # #     self.experimentData = pickle.loads(self.experimentDataRaw)
        # # print([self.experimentDate, self.experimentName])
        # # c.close()
        # # conn.close()

    def newExperiment(self, dateStamp, description, rawData):
        experiment = Experiment()
        experiment.parseRawData(rawData[1], fileName=rawData[0])
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
                  (datetime.datetime.now().strftime("%Y%m%d %H:%M"), dateStamp, description))

        for attrName, tableName in zip(
                ['timePointList', 'titerObjectDict', 'singleExperimentObjectDict', 'replicateExperimentObjectDict'],
                ['TimePoint', 'Titer', 'singleExperiment', 'replicateExperiment']):
            if attrName == 'replicateExperimentObjectDict':
                for key in getattr(experiment, attrName):
                    c.execute(
                        "INSERT INTO replicateExperiment (experimentID, strainID, identifier1, identifier2) VALUES (?, ?,?,?)",
                        (len(self.experimentList),
                         getattr(experiment, attrName)[key].runIdentifier.strainID,
                         getattr(experiment, attrName)[key].runIdentifier.identifier1,
                         getattr(experiment, attrName)[key].runIdentifier.identifier2)
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



        pickle.dump(self.experimentList, open('testpickle.p', 'wb'))

    def getExperiments(self):
        print('There are ', len(self.experimentList), ' experiments')
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
            exptDescription.append({key: data for data, key in zip(row, [elem[0] for elem in c.description])})

        c.close()
        conn.close()
        return exptDescription

    def getStrainInfo_django(self):
        conn = sql.connect(dbName)
        c = conn.cursor()
        c.execute(
            "SELECT experimentID, strainID, identifier1, identifier2 FROM replicateExperiment order by experimentID ASC, strainID ASC, identifier1 ASC, identifier2 ASC")
        data = list(c.fetchall())
        dataList = []
        for row in data:
            dataList.append(list(row))
        c.close()
        conn.close()
        # print(dataList)
        # print(self.experimentList[row[0]-1])
        for row in dataList:
            row.append(self.experimentList[row[0] - 1][2].replicateExperimentObjectDict[row[1] + row[2] + row[3]])
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


        c.execute("""SELECT titerName FROM timeCourseTable_avg WHERE singleTrial_avgID IN  (""" + '?, ' * (
            len(replicateIDs) - 1) + """ ?)"""
                  , tuple(replicateIDs))
        titerList = [row[0] for row in c.fetchall()]
        conn.close()

        uniqueTiters = list(set(titerList))

        return uniqueTiters

    def getAllStrainsByIDSQL(self, experiment_id):
        conn = sql.connect(self.dbName)
        c = conn.cursor()
        experiment_id += 1
        c.execute("SELECT strainID, identifier1, identifier2 FROM replicateExperiment  WHERE (experimentID = ?)",
                  (experiment_id,))
        data = c.fetchall()
        c.close()
        conn.close()
        return data

    def getReplicateExperimentFromID(self, id):
        conn = sql.connect(self.dbName)
        c = conn.cursor()
        c.execute("SELECT experimentID, strainID, identifier1, identifier2 FROM replicateExperiment WHERE (rowid = ?)",
                  (id,))
        data = c.fetchall()
        c.close()
        conn.close()
        a = [data[0], data[1] + data[2] + data[3]]
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

    def printGenericTimeCourse(self, figHandle=[], strainsToPlot=[], titersToPlot=[], removePointFraction=6,
                               shadeErrorRegion=False, showGrowthRates=True, plotCurveFit=True):
        if figHandle == []:
            figHandle = plt.figure(figsize=(12, 8))

        figHandle.set_facecolor('w')

        # if strainsToPlot == []:
        #     strainsToPlot = self.getAllStrainNames()
        # replicateExperimentObjects
        # Plot all product titers if none specified TODO: Add an option to plot OD as well
        if titersToPlot == []:
            titersToPlot = ['OD']  # self.getAllTiters()
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
            figureSize = (12, 6)
        if len(titersToPlot) > 1:
            figureSize = (12, 3.5)
        if len(titersToPlot) > 4:
            figureSize = (12, 7)

        if plotCurveFit == True:
            plotSymbol = 'o'
        else:
            plotSymbol = 'o-'

        figHandle  # .set_size_inches(figureSize, forward=True)
        # plt.figure(figsize=figureSize)
        plt.clf()
        # print(strainsToPlot)
        colors = plt.get_cmap(self.colorMap)(np.linspace(0, 1, len(strainsToPlot)))

        useNewColorScheme = 0
        if useNewColorScheme == 1:
            # Gather some information about the data
            uniques = dict()
            numUniques = dict()
            for identifier, col in zip(['experiment', 'strainID', 'identifier1', 'identifier2'], [0, 1, 2, 3]):
                uniques[identifier] = set(row[col] for row in strainsToPlot)
                numUniques[identifier] = len(uniques[identifier])

            # Check number of unique identifier1s for each of the two identifier2s
            for identifier, col in zip(['experiment', 'strainID', 'identifier1', 'identifier2'], [0, 1, 2, 3]):
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
            colors_test.append(plt.get_cmap(cmap[0])(np.linspace(0.2, 0.9, lenEachUniqueID[0])))
            colors_test.append(plt.get_cmap(cmap[1])(np.linspace(0.2, 0.9, lenEachUniqueID[1])))

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
                ax = plt.subplot(1, len(titersToPlot), pltNum)
            elif len(titersToPlot) < 9:
                ax = plt.subplot(2, (len(titersToPlot) + 1) / 2, pltNum)
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
                if product in replicateToPlot.singleTrialList[0].products or (
                                product == 'OD' and replicateToPlot.singleTrialList[0].OD != None):
                    # print(row)

                    lineLabelsArray[i] = (str(row[0]) + '\t' + row[1] + '\t' + row[2] + '\t' + row[3]).expandtabs()
                    xData = replicateToPlot.t

                    if product == 'OD':
                        scaledTime = replicateToPlot.t
                        # Plot the fit curve
                        if plotCurveFit == True:
                            handleArray[i] = plt.plot(np.linspace(min(scaledTime), max(scaledTime), 50),
                                                      replicateToPlot.avg.OD.returnCurveFitPoints(
                                                          np.linspace(min(replicateToPlot.t), max(replicateToPlot.t),
                                                                      50)),
                                                      '-', lw=1.5, color=colors[colorIndex])[0]

                        # Plot the data
                        temp = plt.errorbar(scaledTime[::removePointFraction],
                                            replicateToPlot.avg.OD.dataVec[::removePointFraction],
                                            replicateToPlot.std.OD.dataVec[::removePointFraction],
                                            lw=2.5, elinewidth=1, capsize=2, fmt=plotSymbol, markersize=5,
                                            color=colors[colorIndex])[0]
                        if plotCurveFit == False: handleArray[i] = temp

                        handleArray[i] = mpatches.Patch(color=colors[colorIndex])

                        # Fill in the error bar range
                        if shadeErrorRegion:
                            plt.fill_between(scaledTime,
                                             replicateToPlot.avg.OD.dataVec + replicateToPlot.std.OD.dataVec,
                                             replicateToPlot.avg.OD.dataVec - replicateToPlot.std.OD.dataVec,
                                             facecolor=colors[colorIndex], alpha=0.1)
                        # Add growth rates at end of curve
                        if showGrowthRates:
                            plt.text(scaledTime[-1] + 0.5,
                                     replicateToPlot.avg.OD.returnCurveFitPoints(
                                         np.linspace(min(replicateToPlot.t), max(replicateToPlot.t), 50))[-1],
                                     '$\mu$ = ' + '{:.2f}'.format(
                                         replicateToPlot.avg.OD.rate[1]) + ' $\pm$ ' + '{:.2f}'.format(
                                         replicateToPlot.std.OD.rate[1]) + ', n=' + str(
                                         len(replicateToPlot.replicateIDs) - len(replicateToPlot.badReplicates)),
                                     verticalalignment='center')
                        ylabel = 'OD$_{600}$'
                    else:

                        scaledTime = replicateToPlot.t

                        handleArray[i] = plt.plot(np.linspace(min(scaledTime), max(scaledTime), 50),
                                                  replicateToPlot.avg.products[product].returnCurveFitPoints(
                                                      np.linspace(min(replicateToPlot.t), max(replicateToPlot.t), 50)),
                                                  '-', lw=0.5, color=colors[colorIndex])[0]
                        handleArray[i] = mpatches.Patch(color=colors[colorIndex])

                        handle_ebar.append(
                            plt.errorbar(replicateToPlot.t, replicateToPlot.avg.products[product].dataVec,
                                         replicateToPlot.std.products[product].dataVec, lw=2.5, elinewidth=1, capsize=2,
                                         fmt='o-', color=colors[colorIndex]))
                        ylabel = product + " Titer (g/L)"
                    minOneLinePlotted = True
                colorIndex += 1
            if minOneLinePlotted == True:
                plt.xlabel(xlabel)
                plt.ylabel(ylabel)
                ymin, ymax = plt.ylim()
                xmin, xmax = plt.xlim()
                plt.xlim([0, xmax * 1.2])
                plt.ylim([0, ymax])
        # plt.style.use('ggplot')
        plt.tight_layout()
        plt.tick_params(right="off", top="off")

        plt.legend(handleArray, lineLabelsArray, bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0, frameon=False)
        plt.subplots_adjust(right=0.7)

        if len(titersToPlot) == 1:
            plt.legend(handleArray, lineLabelsArray, bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0, frameon=False)
            plt.subplots_adjust(right=0.7)
        elif len(titersToPlot) < 4:
            plt.legend(handleArray, lineLabelsArray, bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0, frameon=False)
            plt.subplots_adjust(right=0.75)
        else:
            plt.legend(handleArray, lineLabelsArray, bbox_to_anchor=(1.05, 1.1), loc=6, borderaxespad=0, frameon=False)
            plt.subplots_adjust(right=0.75)

            # Save the figure
            # plt.savefig(os.path.join(os.path.dirname(__file__),'Figures/'+time.strftime('%y')+'.'+time.strftime('%m')+'.'+time.strftime('%d')+" H"+time.strftime('%H')+'-M'+time.strftime('%M')+'-S'+time.strftime('%S')+'.png'))
            # plt.show()