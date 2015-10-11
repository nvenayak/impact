__author__ = 'Naveen'

####### Import packages
from DataObject import *
from pyexcel_xlsx import get_data
from dataParsingFunctions import *
import matplotlib.pyplot as plt
from plottingFunctions import *



####### Define some constants
fileName = "2015.10.08 pTOG Automation Test.xlsx"
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
        tempParsedIdentifier = row[0].split(',')
        print(tempParsedIdentifier)
        if len(tempParsedIdentifier) == 0:
            print(tempParsedIdentifier," <-- not processed")
        if len(tempParsedIdentifier) > 0 :
            tempRunIdentifierObject = runIdentifier()
            tempRunIdentifierObject.strainID = tempParsedIdentifier[0]
        if len(tempParsedIdentifier) > 1 :
            tempRunIdentifierObject.identifier1 = tempParsedIdentifier[1]
        if len(tempParsedIdentifier) > 2 :
            tempRunIdentifierObject.identifier2 = tempParsedIdentifier[2]
        if len(tempParsedIdentifier) > 3 :
            try:
                tempRunIdentifierObject.replicate = int(tempParsedIdentifier[3])#tempParsedIdentifier[1]
            except:
                print("Couldn't parse replicate from ",tempParsedIdentifier)
        tempRunIdentifierObject.titerName = 'OD600'
        tempRunIdentifierObject.titerType = 'OD'
        tempTimeCourseObject = timeCourseObject()
        tempTimeCourseObject.runIdentifier = tempRunIdentifierObject
        tempTimeCourseObject.dataVec = np.array(row[1:])
        tempTimeCourseObject.timeVec = np.array(data[ODDataSheetName][0][1:])
        print(tempTimeCourseObject.getTimeCourseID())
        timeCourseObjectList[tempTimeCourseObject.getTimeCourseID()] = tempTimeCourseObject


        # if tempTimeCourseObject.getTimeCourseID() in timeCourseObjectList:
        #     print('Duplicate Object Found')
        #     #raise Exception("Duplicate time course name found")
        # else:
print(len(timeCourseObjectList))

singleExperimentObjectList = getSingleExperimentObjectListFromTiterObjectList(timeCourseObjectList, 'na', 'OD')

replicateExperimentObjectList = getReplicateExperimentObjectListFromSingleExperimentObjectList(singleExperimentObjectList)
# for key in replicateExperimentObjectList:
    # print(len(replicateExperimentObjectList[key].singleExperimentList))
    # print(replicateExperimentObjectList[key].std.OD.dataVec)


strainsToPlot = list(replicateExperimentObjectList.keys())
strainsToPlot = ['3KO-D1pTOG009IPTG','3KO-D1pTOG009aTc','3KO-D30pTOG009IPTG','3KO-D30pTOG009aTc']
printTimeCourseOD(replicateExperimentObjectList, strainsToPlot)
printGenericTimeCourse(replicateExperimentObjectList,strainsToPlot,['OD'])
plt.show()
# for i in range(0,len(strainsToPlot),4):
#     printTimeCourseOD(replicateExperimentObjectList, strainsToPlot[i:i+3])
#     plt.show()
