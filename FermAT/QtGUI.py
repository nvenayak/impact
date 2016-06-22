__author__ = 'Naveen'
from PyQt4 import QtGui, QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow, Project):
        self.Project = Project()
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(1016, 764)
        MainWindow.setAutoFillBackground(False)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label_3 = QtGui.QLabel(self.centralwidget)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.verticalLayout.addWidget(self.label_3)
        spacerItem = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.verticalLayout.addItem(spacerItem)

        self.comboBox = QtGui.QComboBox(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.comboBox.sizePolicy().hasHeightForWidth())
        self.comboBox.setSizePolicy(sizePolicy)
        self.comboBox.setEditable(False)
        self.comboBox.setObjectName(_fromUtf8("comboBox"))
        for i, row in enumerate(self.Project.getExperiments()):
            self.comboBox.addItem(_fromUtf8(row[1]+' - '+row[2]))

        self.verticalLayout.addWidget(self.comboBox)
        self.verticalLayout_3 = QtGui.QVBoxLayout()
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.label = QtGui.QLabel(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout_3.addWidget(self.label)
        self.verticalLayout.addLayout(self.verticalLayout_3)

        self.tableWidget = QtGui.QTableWidget(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tableWidget.sizePolicy().hasHeightForWidth())
        self.tableWidget.setSizePolicy(sizePolicy)
        self.tableWidget.setMinimumSize(QtCore.QSize(500, 0))
        self.tableWidget.setMaximumSize(QtCore.QSize(100000, 16777215))
        self.tableWidget.setObjectName(_fromUtf8("tableWidget"))
        self.tableWidget.setColumnCount(4)
        self.tableWidget.itemChanged.connect(self.updateStrainsToPlot)
        self.tableWidget.setRowCount(8)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        item = QtGui.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(3, item)
        self.verticalLayout.addWidget(self.tableWidget)

        self.pushButton_clear = QtGui.QPushButton(self.centralwidget)
        self.pushButton_clear.setObjectName(_fromUtf8("pushButton_clear"))
        self.pushButton_clear.clicked.connect(self.clearStrainsToPlot)
        self.pushButton_clear.setText(_translate("MainWindow", "Clear", None))
        self.verticalLayout.addWidget(self.pushButton_clear)

        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setSizeConstraint(QtGui.QLayout.SetMinimumSize)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.label_2 = QtGui.QLabel(self.centralwidget)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout_2.addWidget(self.label_2)

        self.titerCheckBoxList = []
        for titer in self.Project.getAllTiterNames():
            self.titerCheckBoxList.append([QtGui.QCheckBox(self.centralwidget),titer])
            self.titerCheckBoxList[-1][0].setObjectName(_fromUtf8(titer))
            self.titerCheckBoxList[-1][0].setText(_translate("MainWindow", titer, None))
            self.titerCheckBoxList[-1][0].stateChanged.connect(self.updateTitersToPlot)
            self.verticalLayout_2.addWidget(self.titerCheckBoxList[-1][0])
        self.verticalLayout.addLayout(self.verticalLayout_2)

        self.pushButton_updatePlot = QtGui.QPushButton(self.centralwidget)
        self.pushButton_updatePlot.setObjectName(_fromUtf8("pushButton_updatePlot"))
        self.pushButton_updatePlot.clicked.connect(self.updateFigure)
        self.pushButton_updatePlot.setText(_translate("MainWindow", "Update Plot", None))
        self.verticalLayout.addWidget(self.pushButton_updatePlot)

        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_4 = QtGui.QVBoxLayout()
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.figure = plt.figure()
        self.mpl_canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.mpl_toolbar = NavigationToolbar(self.mpl_canvas, self.centralwidget)
        self.verticalLayout_4.addWidget(self.mpl_toolbar)

        self.verticalLayout_4.addWidget(self.mpl_canvas)
        self.horizontalLayout.addLayout(self.verticalLayout_4)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1016, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.menuFile = QtGui.QMenu(self.menubar)
        self.menuFile.setObjectName(_fromUtf8("menuFile"))
        self.menuData = QtGui.QMenu(self.menubar)
        self.menuData.setObjectName(_fromUtf8("menuData"))
        self.menuPlot = QtGui.QMenu(self.menubar)
        self.menuPlot.setObjectName(_fromUtf8("menuPlot"))
        self.menuView = QtGui.QMenu(self.menubar)
        self.menuView.setObjectName(_fromUtf8("menuView"))
        self.menuSort_strains_by = QtGui.QMenu(self.menuView)
        self.menuSort_strains_by.setObjectName(_fromUtf8("menuSort_strains_by"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)
        self.actionImport_data_from_file = QtGui.QAction(MainWindow)
        self.actionImport_data_from_file.setCheckable(False)
        self.actionImport_data_from_file.setChecked(False)
        self.actionImport_data_from_file.setObjectName(_fromUtf8("actionImport_data_from_file"))
        self.actionExport_data_to_file = QtGui.QAction(MainWindow)
        self.actionExport_data_to_file.setObjectName(_fromUtf8("actionExport_data_to_file"))
        self.actionExit = QtGui.QAction(MainWindow)
        self.actionExit.setObjectName(_fromUtf8("actionExit"))
        self.actionData_statistics = QtGui.QAction(MainWindow)
        self.actionData_statistics.setObjectName(_fromUtf8("actionData_statistics"))
        self.action_2 = QtGui.QAction(MainWindow)
        self.action_2.setObjectName(_fromUtf8("action_2"))

        self.actionStrain_ID = QtGui.QAction(MainWindow)
        self.actionStrain_ID.setObjectName(_fromUtf8("actionStrain_ID"))
        self.actionStrain_ID.triggered.connect(self.updateSortByStrain)

        self.actionIdentifier_1 = QtGui.QAction(MainWindow)
        self.actionIdentifier_1.setObjectName(_fromUtf8("actionIdentifier_1"))
        self.actionIdentifier_1.triggered.connect(self.updateSortById1)


        self.actionIdentifier_2 = QtGui.QAction(MainWindow)
        self.actionIdentifier_2.setObjectName(_fromUtf8("actionIdentifier_2"))
        self.actionIdentifier_2.triggered.connect(self.updateSortById2)


        self.menuFile.addAction(self.actionExit)
        self.menuData.addAction(self.actionImport_data_from_file)
        self.menuData.addAction(self.actionExport_data_to_file)
        self.menuData.addSeparator()
        self.menuData.addAction(self.actionData_statistics)
        self.menuPlot.addAction(self.action_2)
        self.menuSort_strains_by.addAction(self.actionStrain_ID)
        self.menuSort_strains_by.addAction(self.actionIdentifier_1)
        self.menuSort_strains_by.addAction(self.actionIdentifier_2)
        self.menuView.addAction(self.menuSort_strains_by.menuAction())
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuData.menuAction())
        self.menubar.addAction(self.menuPlot.menuAction())
        self.menubar.addAction(self.menuView.menuAction())

        # Prepare list of all check boxes possible
        data = self.Project.getAllStrainNames()

        self.strainCheckBoxList = []
        for i, row in enumerate(data):
            item = QtGui.QTableWidgetItem('')
            item.setFlags(QtCore.Qt.ItemIsUserCheckable |
                          QtCore.Qt.ItemIsEnabled)
            item.setCheckState(QtCore.Qt.Unchecked)
            self.strainCheckBoxList.append([row[0],row[1],row[2],row[3],item,row[4]])

        self.comboBox.activated.connect(self.experimentSelect)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

        self.sortByCol = 0
        self.sortComboBox = dict()
        self.selectedStrain = 'All'
        self.selectedid1 = 'All'
        self.selectedid2 = 'All'

    def updateSortByStrain(self):
        self.sortByCol = 1
        self.experimentSelect(self.selectedId-1)
    def updateSortById1(self):
        self.sortByCol = 2
        self.experimentSelect(self.selectedId-1)
    def updateSortById2(self):
        self.sortByCol = 3
        self.experimentSelect(self.selectedId-1)


    def updateTitersToPlot(self):
        print('in here')
        self.titersToPlot = []
        for row in self.titerCheckBoxList:
            if row[0].checkState() == QtCore.Qt.Checked:
                self.titersToPlot.append(row[1])


    def updateStrainsToPlot(self):
        self.strainsToPlot = []
        for row in self.strainCheckBoxList:
            if row[4].checkState() == QtCore.Qt.Checked:
                self.strainsToPlot.append(row)
        # self.updateFigure()

    def updateFigure(self):
        self.Project.printGenericTimeCourse(figHandle = self.figure, strainsToPlot=self.strainsToPlot, titersToPlot=self.titersToPlot, removePointFraction=4, shadeErrorRegion=False, showGrowthRates=True, plotCurveFit=True )
        self.mpl_canvas.draw()

    def selectStrain(self, selection):  self.selectedStrain = selection
    def selectid1(self, selection): self.selectedid1 = selection
    def selectid2(self, selection): self.selectedid2 = selection

    def clearStrainsToPlot(self): [row[4].setCheckState(QtCore.Qt.Unchecked) for row in self.strainCheckBoxList]

    def selectStrainsUpdate(self):
        for row in self.strainCheckBoxList:
            if row[0] == self.selectedId and (row[1] == self.selectedStrain or self.selectedStrain == 'All') \
                    and (row[2] == self.selectedid1 or self.selectedid1 == 'All')\
                    and (row[3] == self.selectedid2 or self.selectedid2 == 'All'):
                row[4].setCheckState(QtCore.Qt.Checked)

    def experimentSelect(self, id):
        # data = self.Project.getAllStrainsByIDSQL(id)
        id += 1
        self.selectedId = id
        for row in range(self.tableWidget.rowCount()):
            self.tableWidget.takeItem(row,3)

        for col, key in zip(range(3),['strain','id1','id2']):
            uniques = sorted(list(set(row[col+1] for row in self.strainCheckBoxList if row[0] == id)))
            self.sortComboBox[key] = QtGui.QComboBox()
            if key == 'strain': self.sortComboBox[key].activated[str].connect(self.selectStrain)
            if key == 'id1': self.sortComboBox[key].activated[str].connect(self.selectid1)
            if key == 'id2': self.sortComboBox[key].activated[str].connect(self.selectid2)
            self.sortComboBox[key].addItem('All')
            [self.sortComboBox[key].addItem(unique) for unique in uniques]
            self.tableWidget.setCellWidget(0,col,self.sortComboBox[key])

        self.selectStrainsPushButton = QtGui.QPushButton(self.centralwidget)
        self.selectStrainsPushButton.clicked.connect(self.selectStrainsUpdate)
        self.tableWidget.setCellWidget(0,3,self.selectStrainsPushButton)
        self.selectStrainsPushButton.setText(_translate("MainWindow", "Select", None))
        item = QtGui.QTableWidgetItem()
        item.setText(_translate("MainWindow", "", None))
        self.tableWidget.setVerticalHeaderItem(0, item)

        numRows = len([row[0] for row in self.strainCheckBoxList if row[0] == id])+1

        self.tableWidget.setRowCount(numRows)
        for i in range(numRows-1):
            item = QtGui.QTableWidgetItem()
            item.setText(_translate("MainWindow", str(i+1), None))
            self.tableWidget.setVerticalHeaderItem(i+1, item)



        index = 1
        sortedStrains = sorted(self.strainCheckBoxList, key=lambda x: x[self.sortByCol])

        for row in sortedStrains:
            if row[0] == id:
                for j in range(3):
                    item = QtGui.QTableWidgetItem()
                    item.setText(_translate("MainWindow", row[j+1], None))
                    self.tableWidget.setItem(index,j,item)
                self.tableWidget.setItem(index,3,row[4])
                index += 1

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "FermAT: Fermentation Data Analysis and Plotting Inventory", None))
        self.label_3.setText(_translate("MainWindow", "<html><head/><body><p align=\"center\"><span style=\" font-size:14pt; font-weight:600;\">Data Browser</span></p></body></html>", None))
        # self.comboBox.setItemText(0, _translate("MainWindow", "Experiment #1", None))
        # self.comboBox.setItemText(1, _translate("MainWindow", "Experiment #2", None))
        # self.comboBox.setItemText(2, _translate("MainWindow", "Experiment #3", None))
        self.label.setText(_translate("MainWindow", "<html><head/><body><p align=\"center\"><span style=\" font-size:10pt; font-weight:600;\">Strains</span></p></body></html>", None))


        # self.tableWidget.setSortingEnabled(__sortingEnabled)
        self.label_2.setText(_translate("MainWindow", "<html><head/><body><p align=\"center\"><span style=\" font-size:10pt; font-weight:600;\">Titers</span></p></body></html>", None))
        # self.checkBox_4.setText(_translate("MainWindow", "CheckBox", None))
        self.menuFile.setTitle(_translate("MainWindow", "File", None))
        self.menuData.setTitle(_translate("MainWindow", "Data", None))
        self.menuPlot.setTitle(_translate("MainWindow", "Plot", None))
        self.menuView.setTitle(_translate("MainWindow", "View", None))
        self.menuSort_strains_by.setTitle(_translate("MainWindow", "Sort strains by..", None))
        self.actionImport_data_from_file.setText(_translate("MainWindow", "Import data from file", None))
        self.actionExport_data_to_file.setText(_translate("MainWindow", "Export data to file", None))
        self.actionExit.setText(_translate("MainWindow", "Exit", None))
        self.actionData_statistics.setText(_translate("MainWindow", "Data statistics", None))
        self.action_2.setText(_translate("MainWindow", "Options", None))
        self.actionStrain_ID.setText(_translate("MainWindow", "Strain ID", None))
        self.actionIdentifier_1.setText(_translate("MainWindow", "Identifier 1", None))
        self.actionIdentifier_2.setText(_translate("MainWindow", "Identifier 2", None))

class fDAPI_login(object):
    def __init__(self):
       # SQLite stuff
        # Initialize database
        conn = sql.connect('userDB.db')
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS %s (username TEXT, password TEXT) "% "userpass")
        conn.commit()
        c.close()
        conn.close()

class mainWindow(QtGui.QDialog):
    def __init__(self,Project,parent=None):
        super(mainWindow, self).__init__(parent)
        self.Project = Project
        # Populate the experimental data combo box
        projectData = Project.getExperiments()
        print(projectData[0][0])
        experimentComboBox = QtGui.QComboBox(self)
        for i in range(len(projectData)):
            experimentComboBox.addItem(projectData[i][1])#+' - '+exptDescrpt[i])
        experimentComboBox.activated[str].connect(self.exptComboBoxSelect)

        # Initiate experiment list
        # experimentListView = QtGui.QListView()
        # sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        # sizePolicy.setHorizontalStretch(0)
        # sizePolicy.setVerticalStretch(0)
        # experimentListView.setSizePolicy(sizePolicy)

        self.checkBox = dict()
        self.titersCheckBox = dict()


        # top bar
        topBarHorzLayout = QtGui.QHBoxLayout()
        topBarButtons = []
        for button in ['Input Data','Plot Options','Visual Options']:
            topBarButtons.append(QtGui.QPushButton(button))
            topBarHorzLayout.addWidget(topBarButtons[-1])

        # data selection layout
        self.dataSelectionLayout = QtGui.QVBoxLayout()
        self.dataSelectionLayout.addWidget(experimentComboBox)
        self.strainsToPlotVertLayout = QtGui.QVBoxLayout()
        self.dataSelectionLayout.addLayout(self.strainsToPlotVertLayout)
        # self.dataSelectionLayout.addWidget(QtGui.QSpacerItem(1,0))
        self.titersLayout = QtGui.QVBoxLayout()
        self.dataSelectionLayout.addLayout(self.titersLayout)

        # dataSelectionLayout.addWidget(experimentListView)

        # Plotting stuff
        self.figure = plt.figure()
        # self.strainsToPlot = self.newProjectContainer.getAllStrains()
        # self.titersToPlot = self.newProjectContainer.getAllTiters()
        self.sortBy = 'identifier1'
        self.plotType = 'printGenericTimeCourse'
        self.showGrowthRates = True
        self.plotCurveFit = True

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.mpl_canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.mpl_toolbar = NavigationToolbar(self.mpl_canvas, self)

        plotVertLayout = QtGui.QVBoxLayout()
        plotVertLayout.addWidget(self.mpl_toolbar)
        plotVertLayout.addWidget(self.mpl_canvas)


        bottomHorzLayout = QtGui.QHBoxLayout()
        bottomHorzLayout.addLayout(self.dataSelectionLayout)
        bottomHorzLayout.addLayout(plotVertLayout)

        mainVertLayout = QtGui.QVBoxLayout()
        mainVertLayout.addLayout(topBarHorzLayout)
        mainVertLayout.addLayout(bottomHorzLayout)


        self.setLayout(mainVertLayout)

    def exptComboBoxSelect(self,exptName):
        # On selection of a new experiment, must clear all plotting data
        if len(self.checkBox)>0:
            for key in self.checkBox:
                self.checkBox[key].close()

        if len(self.titersCheckBox) > 0:
            for key in self.titersCheckBox:
                self.titersCheckBox[key].close()

        # Set the current object as the selected experiment
        self.newProjectContainer = [experiment[2] for experiment in self.Project.experimentList if experiment[0] == exptName][0]

        # Populate the list of strains and add to layout
        self.strainsToPlot = self.newProjectContainer.get_strains()
        # self.strainsToPlot = []
        for strain in self.strainsToPlot:
            self.checkBox[strain] = (QtGui.QCheckBox(strain,self))
            self.checkBox[strain].stateChanged.connect(self.updateStrainsToPlot)
            self.strainsToPlotVertLayout.addWidget(self.checkBox[strain])
        # for key in self.checkBox:


        # self.dataSelectionLayout.addLayout(self.strainsToPlotVertLayout)


        # Populate list of titers and add to layout
        self.titersToPlot = self.newProjectContainer.get_titers()
        #
        #
        #
        for titer in self.titersToPlot:
            self.titersCheckBox[titer] = (QtGui.QCheckBox(titer,self))
            self.titersCheckBox[titer].stateChanged.connect(self.updateTiters)
            self.titersLayout.addWidget(self.titersCheckBox[titer])



        self.sortBy = 'identifier1'
        self.plotType = 'printGenericTimeCourse'

        # self.updateFigure()
        # pass
        # for experimentDate in Project.getExperiments():

    def updatePlotType(self, plotType):
        self.plotType = plotType
        self.updateFigure()

    def updateSortBy(self, sortBy):
        # print('in here')
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

    def updateOption(self):
        for checkBoxKey in self.optionsCheckBox:
            if self.optionsCheckBox[checkBoxKey].checkState() == QtCore.Qt.Checked:
                setattr(self,checkBoxKey,True)
            else:
                setattr(self,checkBoxKey,False)
        self.updateFigure()

    def updateFigure(self):
        #getattr(self.newProjectContainer,self.plotType)(self.figure, self.strainsToPlot, self.sortBy)
        if self.plotType == 'printGenericTimeCourse':
            self.newProjectContainer.printGenericTimeCourse(figHandle=self.figure, strainsToPlot=self.strainsToPlot,titersToPlot=self.titersToPlot, removePointFraction=4, plotCurveFit=self.plotCurveFit, showGrowthRates=self.showGrowthRates)
        if self.plotType == 'printGrowthRateBarChart':
            self.newProjectContainer.printGrowthRateBarChart(self.figure, self.strainsToPlot, self.sortBy)
        if self.plotType == 'printAllReplicateTimeCourse':
            self.newProjectContainer.printAllReplicateTimeCourse(self.figure, self.strainsToPlot)
        self.mpl_canvas.draw()

class Window(QtGui.QDialog):
    def __init__(self, newProjectContainer, parent=None):
        super(Window, self).__init__(parent)
        self.newProjectContainer = newProjectContainer

        # a figure instance to plot on
        self.figure = plt.figure()
        self.strainsToPlot = self.newProjectContainer.get_strains()
        self.titersToPlot = self.newProjectContainer.get_titers()
        self.sortBy = 'identifier1'
        self.plotType = 'printGenericTimeCourse'
        self.showGrowthRates = True
        self.plotCurveFit = True
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

        self.optionsCheckBox = dict()
        for key in ['showGrowthRates','plotCurveFit']:
            self.optionsCheckBox[key] = QtGui.QCheckBox(key,self)
            self.optionsCheckBox[key].stateChanged.connect(self.updateOption)
            self.optionsCheckBox[key].setChecked = True

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

        optionsVertLayout = QtGui.QVBoxLayout()
        for option in self.optionsCheckBox:
            optionsVertLayout.addWidget(self.optionsCheckBox[option])

        horLayout = QtGui.QHBoxLayout()
        horLayout.addLayout(leftVertLayout)
        horLayout.addLayout(rightVertLayout)
        horLayout.addLayout(titersVertLayout)
        horLayout.addLayout(optionsVertLayout)
        self.setLayout(horLayout)

    def updatePlotType(self, plotType):
        self.plotType = plotType
        self.updateFigure()

    def updateSortBy(self, sortBy):
        # print('in here')
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

    def updateOption(self):
        for checkBoxKey in self.optionsCheckBox:
            if self.optionsCheckBox[checkBoxKey].checkState() == QtCore.Qt.Checked:
                setattr(self,checkBoxKey,True)
            else:
                setattr(self,checkBoxKey,False)
        self.updateFigure()
    # def updateBadReplicates(self):
    #     for replicateCheckBoxKey in self.replicateCheckBox:



    def updateFigure(self):
        #getattr(self.newProjectContainer,self.plotType)(self.figure, self.strainsToPlot, self.sortBy)
        if self.plotType == 'printGenericTimeCourse':
            self.newProjectContainer.printGenericTimeCourse(figHandle=self.figure, strainsToPlot=self.strainsToPlot,titersToPlot=self.titersToPlot, removePointFraction=4, plotCurveFit=self.plotCurveFit, showGrowthRates=self.showGrowthRates)
        if self.plotType == 'printGrowthRateBarChart':
            self.newProjectContainer.printGrowthRateBarChart(self.figure, self.strainsToPlot, self.sortBy)
        if self.plotType == 'printAllReplicateTimeCourse':
            self.newProjectContainer.printAllReplicateTimeCourse(self.figure, self.strainsToPlot)
        self.canvas.draw()
