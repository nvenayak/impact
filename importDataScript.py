__author__ = 'Naveen'

####### Import packages
from DataObject import *
from pyexcel_xlsx import get_data
from dataParsingFunctions import *
from plottingFunctions import *
import matplotlib.pyplot as plt
import copy
import time
import tkinter as tk

####### Define some constants
fileName = "2015.05.19.LactateStoryData.xlsx"
substrateName = 'Glucose'
titerDataSheetName = "titers"

####### Get data from xlsx file
data = get_data(fileName)

####### Check for correct data for import
# if 'OD' not in data.keys():
#     raise Exception("No sheet named 'OD' found")

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
                tempTimePointCollection[key] = timePoint(copy.copy(tempRunIdentifierObject), key, tempRunIdentifierObject.t, data['titers'][i][titerNameColumn[key]])
                #print(tempTimePointCollection[key].runIdentifier.titerName)
            timePointCollection.append(tempTimePointCollection.copy())
        else:
            skippedLines += 1
    else:
        skippedLines += 1

print("Number of lines skipped: ",skippedLines)


newProjectContainer = projectContainer()
######## Combine time points into timeCourseObjects
titerObjectList = getTiterObjectListFromTimePointCollection(timePointCollection)

# ----- Add the data to the projectContainer ----------------
newProjectContainer.parseTiterObjectCollection(titerObjectList, 'titer')

# ######## List Experiment names
# print("Experiment Name\t# Replicates\t#Products")
# for key in replicateExperimentObjectList:
#     print(key,"\t\t",len(replicateExperimentObjectList[key].singleExperimentList))


######## Strains To Plot
strainsToPlotList = [['pTOG009IPTG','pTOG009aTc'],['pTOG007IPTG','pTOG007aTc'],['pTOG008IPTG','pTOG08aTc'],['pTOG0010IPTG','pTOG010aTc'],['lacI  pKDL071']]

strainsToPlot = []
for strainsToPlotPair in strainsToPlotList:
    for strainToPlot in strainsToPlotPair:
        strainsToPlot.append(strainToPlot)

strainsToPlot = ['lacI  pKDL071','pTOG009IPTG','pTOG009aTc']
# strainsToPlot = ['pTOG009IPTG','pTOG009aTc']

newProjectContainer.printGenericTimeCourse(strainsToPlot, ["Acetate","Ethanol","Lactate"])
newProjectContainer.printEndPointYield(strainsToPlot, 1)
newProjectContainer.printYieldTimeCourse(strainsToPlot)

plt.show()