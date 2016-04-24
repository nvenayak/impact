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

import numpy as np
from scipy.signal import savgol_filter
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from lmfit import Model
from pyexcel_xlsx import get_data
from PyQt4 import QtGui, QtCore
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import dill as pickle

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
        self.actionIdentifier_1.triggered.connect(self.updateSortById2)


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

    def updateSortByStrain(self):   self.sortByCol = 1
    def updateSortById1(self):  self.sortByCol = 2
    def updateSortById2(self):  self.sortByCol = 3

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
            uniques = list(set(row[col+1] for row in self.strainCheckBoxList if row[0] == id))
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
        MainWindow.setWindowTitle(_translate("MainWindow", "fDAPI: Fermentation Data Analysis and Plotting Inventory", None))
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
        self.strainsToPlot = self.newProjectContainer.getAllStrains()
        # self.strainsToPlot = []
        for strain in self.strainsToPlot:
            self.checkBox[strain] = (QtGui.QCheckBox(strain,self))
            self.checkBox[strain].stateChanged.connect(self.updateStrainsToPlot)
            self.strainsToPlotVertLayout.addWidget(self.checkBox[strain])
        # for key in self.checkBox:


        # self.dataSelectionLayout.addLayout(self.strainsToPlotVertLayout)


        # Populate list of titers and add to layout
        self.titersToPlot = self.newProjectContainer.getAllTiters()
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
        self.strainsToPlot = self.newProjectContainer.getAllStrains()
        self.titersToPlot = self.newProjectContainer.getAllTiters()
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

class Project(object):
    """
    """

    colorMap = 'Set3'

    def __init__(self):

        # c.execute("CREATE TABLE IF NOT EXISTS %s (datestamp TEXT, strainID TEXT, identifier1 TEXT, identifier2 TEXT, replicate INTEGER, time REAL, titerName TEXT, titerType TEXT, timeVec BLOB, dataVec BLOB) "%table)

        #print('Searching for available databases...')
        # conn = sql.connect('defaultProjectDatabase.db')
        # c = conn.cursor()
        # c.execute(
        #     'CREATE TABLE IF NOT EXISTS experimentTable(datestamp TEXT, description TEXT, data BLOB)'
        # )

        # #load data
        # c.execute("SELECT datestamp, description, data from experimentTable")
        # data = c.fetchall()
        # if len(data) > 0:
        #     self.experimentData = []
        #     self.experimentDescription = []
        #     self.experimentData = []
        #     print(data[0][2])
        #     print('break')
        #     print(str(data[0][2]))
        #     a = pickle.loads(str(data[0][2]))
        #     print('set a')
        #     for row in data:
        #         self.experimentDate = row[0]
        #         self.experimentDescription = row[1]
        #         self.experimentData = pickle.loads(str(row[2]))

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
        experiment.parseRawData(rawData[0],rawData[1])
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

    def getAllStrainNames(self):
        conn = sql.connect(self.dbName)
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
                for singleExperiment in experiment[2].replicateExperimentObjectDict[key].singleExperimentList:
                    for product in singleExperiment.products:
                       titerNames.append(product)

                    if singleExperiment.OD != None:
                        titerNames.append('OD')
        uniqueTiterNames = set(titerNames)

        # titersToPlot = [[[product for product in singleExperiment.products] for singleExperiment in self.replicateExperimentObjectDict[key].singleExperimentList] for key in self.replicateExperimentObjectDict]
        #
        #
        # titersToPlot = [[[product for product in singleExperiment.products] for singleExperiment in self.replicateExperimentObjectDict[key].singleExperimentList] for key in self.replicateExperimentObjectDict]
        #
        # # Flatten list and find the uniques
        # titersToPlot = [y for x in titersToPlot for y in x]
        # titersToPlot =  list(set([y for x in titersToPlot for y in x]))
        #
        # ODList = [[singleExperiment.OD for singleExperiment in self.replicateExperimentObjectDict[key].singleExperimentList] for key in self.replicateExperimentObjectDict]
        # ODList = list(set([y for x in ODList for y in x]))
        #
        # # print(ODList)
        # if ODList[0] != None:
        #     titersToPlot.append('OD')

        return uniqueTiterNames

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
                    if product in row[5].singleExperimentList[0].products:
                        temp.append(True)
                    else:
                        temp.append(False)
                titersToPlotPerStrain.append(temp)
        titerNames = []
        for experiment in self.experimentList:
            for key in experiment[2].replicateExperimentObjectDict:
                for singleExperiment in experiment[2].replicateExperimentObjectDict[key].singleExperimentList:
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
                if product in replicateToPlot.singleExperimentList[0].products or (product == 'OD' and replicateToPlot.singleExperimentList[0].OD != None):
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


class Experiment(object):
    colorMap = 'Set2'
    def __init__(self):
        # Initialize variables
        self.timePointList = []#dict()
        self.titerObjectDict = dict()
        self.singleExperimentObjectDict = dict()
        self.replicateExperimentObjectDict = dict()


        # SQLite stuff
        # Initialize database
        conn = sql.connect('temptSQLite3db.db')
        c = conn.cursor()
        for table in ['timePointTable','timeCourseTable','singleExperimentTable','replicateExperimentTable']:
            c.execute("CREATE TABLE IF NOT EXISTS %s (datestamp TEXT, strainID TEXT, identifier1 TEXT, identifier2 TEXT, replicate INTEGER, time REAL, titerName TEXT, titerType TEXT, timeVec BLOB, dataVec BLOB) "%table)
        conn.commit()
        c.close()
        conn.close()


    def plottingGUI(self):
        app = QtGui.QApplication(sys.argv)

        main = Window(self)
        main.showMaximized()

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
                temp_run_identifier_object = RunIdentifier()
                if type("asdf") == type(row[0]):
                    temp_run_identifier_object.getRunIdentifier(row[0])
                    temp_run_identifier_object.titerName = 'OD600'
                    temp_run_identifier_object.titerType = 'OD'
                    tempTimeCourseObject = TimeCourse()
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
        for singleExperiment in self.replicateExperimentObjectDict[strainToPlot[0]].singleExperimentList:
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

class TimePoint(object):
    def __init__(self, runID, titerName, t, titer):
        self.runIdentifier = runID
        self.titerName = titerName
        self. t = t
        self.titer = titer

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
            # Check if the parameter is a lambda function
            temp = dict()
            for hint in ['guess','min','max']:
                if type(param[hint]) == type(lambda x: 0):
                    try:
                        temp[hint] = param[hint](data)
                    except Exception as e:
                        print(param[hint])
                        print(data)
                        raise Exception(e)

                else:
                    temp[hint] = param[hint]

            self.gmod.set_param_hint(param['name'],
                                     value=temp['guess'],
                                     min=temp['min'],
                                     max=temp['max'])
        params = self.gmod.make_params()
        result = self.gmod.fit(data,params,t=t,method=method)
        return result

class TimeCourse(Titer):
    """
    Child of :class:`~Titer` which contains curve fitting relevant to time course data
    """
    def __init__(self):
        Titer.__init__(self)
        self.timeVec = None
        self._dataVec = None
        self.rate = None

        # Parameters
        self.removeDeathPhaseFlag = True
        self.useFilteredDataFlag = False
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
    def dataVec(self):
        if self.useFilteredDataFlag == True:
            return savgol_filter(self._dataVec,self.savgolFilterWindowSize,3)
        else:
            return self._dataVec

    @dataVec.setter
    def dataVec(self, dataVec):
        self._dataVec = dataVec
        self.deathPhaseStart = len(dataVec)

        if self.removeDeathPhaseFlag == True:
            if np.max(dataVec) > 0.2:
                try:
                    filteredData = savgol_filter(dataVec,51,3)
                    diff = np.diff(filteredData)

                    count=0
                    # print(diff)
                    flag = 0
                    for i in range(len(diff)-1):
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

        # self._dataVec = dataVec
        # print(self.deathPhaseStart)
        if len(self.dataVec)>6:
            self.calcExponentialRate()

    def returnCurveFitPoints(self, t):
       return self.curveFitObjectDict[self.fitType].growthEquation(t, *self.rate)

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

class ReplicateTrial(object):
    """
    This object stores SingleTrial objects and calculates statistics on these replicates for each of the
    titers which are stored within it
    """
    def __init__(self):
        self.avg = SingleTrialDataShell()
        self.std = SingleTrialDataShell()
        self.t = None
        self.singleExperimentList = []
        self.runIdentifier = RunIdentifier()
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
        """
        Add a SingleTrial object to this list of replicates

        mewReplicateExperiment: A :class:`~SingleTrial` object
        """
        self.singleExperimentList.append(newReplicateExperiment)
        if len(self.singleExperimentList)==1:
            self.t = self.singleExperimentList[0].t
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

        for singleExperiment in self.singleExperimentList:
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
                    tempRate[testReplicate] = np.sum(np.std([singleExperimentObject.OD.dataVec for singleExperimentObject in self.singleExperimentList
                                                      if singleExperimentObject.runIdentifier.replicate != testReplicate], axis=0))   # Perform this test only on growth rate
                minDevKey = min(tempRate,key=tempRate.get)
                tempRateKey = minDevKey

                if tempRate[tempRateKey]/np.mean([tempRate[tempRateKey2] for tempRateKey2 in tempRate if tempRateKey2 != tempRateKey]) < 0.6 :
                    self.badReplicates.append(int(tempRateKey))

            # Calculate the statistics on the data and parameters
            self.avg.OD.dataVec = np.mean([singleExperimentObject.OD.dataVec for singleExperimentObject in self.singleExperimentList if singleExperimentObject.runIdentifier.replicate not in self.badReplicates], axis=0)
            self.std.OD.dataVec = np.std([singleExperimentObject.OD.dataVec for singleExperimentObject in self.singleExperimentList if singleExperimentObject.runIdentifier.replicate not in self.badReplicates], axis=0)
            self.avg.OD.rate = np.mean([singleExperimentObject.OD.rate for singleExperimentObject in self.singleExperimentList if singleExperimentObject.runIdentifier.replicate not in self.badReplicates], axis=0)
            self.std.OD.rate = np.std([singleExperimentObject.OD.rate for singleExperimentObject in self.singleExperimentList if singleExperimentObject.runIdentifier.replicate not in self.badReplicates], axis=0)

        if productFlag == 1:
            for key in self.singleExperimentList[0].products:
                self.avg.products[key] = TimeCourseShell()
                self.std.products[key] = TimeCourseShell()
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