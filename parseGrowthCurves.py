__author__ = 'Naveen'

####### Import packages
from DataObject import *
from pyexcel_xlsx import get_data
from dataParsingFunctions import *
import matplotlib.pyplot as plt
import time
import tkinter as tk

####### Define some constants
fileName = "ODTest.xlsx"
substrateName = 'Glucose'
titerDataSheetName = "titers"
ODDataSheetName = 'OD'


###############################

####### Get data from xlsx file
data = get_data(fileName)

####### Check for correct data for import
if 'OD' not in data.keys():
    raise Exception("No sheet named 'OD' found")

# if 'titers' not in data.keys():
#     raise Exception("No sheet named 'titers' found")

skippedLines = 0

timeCourseObjectList = dict()

for row in data[ODDataSheetName][1:]:
    if type("asdf") == type(row[0]):
        print('1')
        tempParsedIdentifier = row[0].split(',')
        if len(tempParsedIdentifier) == 0:
            print(tempParsedIdentifier," <-- not processed")
        if len(tempParsedIdentifier) > 1 :
            tempRunIdentifierObject = runIdentifier()
            tempRunIdentifierObject.strainID = tempParsedIdentifier[0]
        if len(tempParsedIdentifier) > 2 :
            tempRunIdentifierObject.identifier1 = tempParsedIdentifier[1]
        if len(tempParsedIdentifier) > 3 :
            tempRunIdentifierObject.identifier2 = tempParsedIdentifier[2]
        if len(tempParsedIdentifier) > 4 :
            tempRunIdentifierObject.replicate = int(tempParsedIdentifier[3])#tempParsedIdentifier[1]
        tempTimeCourseObject = timeCourseObject()
        tempTimeCourseObject.uniqueID = tempRunIdentifierObject
        tempTimeCourseObject.dataVec = np.array(row[1:])
        tempTimeCourseObject.timeVec = data[ODDataSheetName][0][1:]
        if tempTimeCourseObject.getTimeCourseID() in timeCourseObjectList:
            print('Duplicate Object Found')
            #raise Exception("Duplicate time course name found")
        else:
            timeCourseObjectList[tempTimeCourseObject.getTimeCourseID()] = tempTimeCourseObject

singleExperimentObjectList = getSingleExperimentObjectListFromTiterObjectList(timeCourseObjectList, 'na', 'OD')
replicateExperimentObjectList = getReplicateExperimentObjectListFromSingleExperimentObjectList(singleExperimentObjectList)


#
# ######## Parse the titer data into single experiment object list
# ### NOTE: THIS PARSER IS NOT GENERIC AND MUST BE MODIFIED FOR YOUR SPECIFIC INPUT TYPE ###
# for i in range(4, len(data['titers'])):
#     if type("asdf") == type(data['titers'][i][0]):  #Check if the data is a string
#         tempParsedIdentifier = data['titers'][i][0].split(',')  #Parse the string using comma delimiter
#         if len(tempParsedIdentifier) >= 3:  #Ensure corect number of identifiers TODO make this general
#             tempRunIdentifierObject = runIdentifier()
#             tempParsedStrainIdentifier = tempParsedIdentifier[0].split("+")
#             tempRunIdentifierObject.strainID = tempParsedStrainIdentifier[0]
#             tempRunIdentifierObject.identifier1 = tempParsedStrainIdentifier[1]
#             # tempRunIdentifierObject.identifier2 = tempParsedIdentifier[2]
#             tempParsedReplicate = tempParsedIdentifier[1].split('=')
#             tempRunIdentifierObject.replicate = int(tempParsedReplicate[1])#tempParsedIdentifier[1]
#             tempParsedTime = tempParsedIdentifier[2].split('=')
#             tempRunIdentifierObject.t = float(tempParsedTime[1])#tempParsedIdentifier[2]
#             for key in tempTimePointCollection:
#                 tempTimePointCollection[key] = timePoint(tempRunIdentifierObject, key, tempRunIdentifierObject.t, data['titers'][i][titerNameColumn[key]])
#             timePointCollection.append(tempTimePointCollection.copy())
#         else:
#             skippedLines += 1
#     else:
#         skippedLines += 1