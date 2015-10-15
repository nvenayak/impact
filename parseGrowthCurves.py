__author__ = 'Naveen'

####### Import packages
from DataObject import *
from pyexcel_xlsx import get_data
from dataParsingFunctions import *
import matplotlib.pyplot as plt
from plottingFunctions import *
import pickle


####### Define some constants
fileName = "2015.10.08 pTOG Automation Test.xlsx"
substrateName = 'Glucose'
titerDataSheetName = "titers"
ODDataSheetName = 'OD'



####### Get data from xlsx file
data = get_data(fileName)




####### Check for correct data for import
if 'OD' not in data.keys():
    raise Exception("No sheet named 'OD' found")

# if 'titers' not in data.keys():
#     raise Exception("No sheet named 'titers' found")


####### Parse data into timeCourseObjects
skippedLines = 0
timeCourseObjectList = dict()
for row in data[ODDataSheetName][1:]:
    tempRunIdentifierObject = runIdentifier()
    if type("asdf") == type(row[0]):
        tempRunIdentifierObject.getRunIdentifier(row[0])
        tempRunIdentifierObject.titerName = 'OD600'
        tempRunIdentifierObject.titerType = 'OD'
        tempTimeCourseObject = timeCourseObject()
        tempTimeCourseObject.runIdentifier = tempRunIdentifierObject
        tempTimeCourseObject.timeVec = np.array(np.divide(data[ODDataSheetName][0][1:], 3600)) #Data in seconds, data required to be in hours
        tempTimeCourseObject.dataVec = np.array(row[1:])
        timeCourseObjectList[tempTimeCourseObject.getTimeCourseID()] = tempTimeCourseObject

        # if tempTimeCourseObject.getTimeCourseID() in timeCourseObjectList:
        #     print('Duplicate Object Found')
        #     #raise Exception("Duplicate time course name found")
        # else:
print("Parsed timeCourseObjects from data: ",len(timeCourseObjectList))


## Add the data to the project
newProjectContainer = projectContainer()
newProjectContainer.parseTiterObjectCollection(timeCourseObjectList, 'OD')

pickle.dump(newProjectContainer, open('testpickle.p','wb'))

strainsToPlot = list(newProjectContainer.replicateExperimentObjectDict.keys())

strainsToPlot = [key for key in newProjectContainer.replicateExperimentObjectDict if newProjectContainer.replicateExperimentObjectDict[key].runIdentifier.identifier1 != '']
strainsToPlot.sort()


#strainsToPlot = ['3KO-D1pTOG009IPTG','3KO-D1pTOG009aTc','3KO-D30pTOG009IPTG','3KO-D30pTOG009aTc','3KO-D1pTOG010IPTG','3KO-D1pTOG010aTc','3KO-D30pTOG010IPTG','3KO-D30pTOG010aTc']

sortBy = 'identifier1'
#printGrowthRateBarChart(replicateExperimentObjectList, strainsToPlot)
#printTimeCourseOD(replicateExperimentObjectList, strainsToPlot)
for sortBy in ['strainID','identifier1','identifier2']:
    printGrowthRateBarChart(newProjectContainer.replicateExperimentObjectDict, strainsToPlot, sortBy)
printGenericTimeCourse(newProjectContainer.replicateExperimentObjectDict,strainsToPlot,['OD'])
plt.show()
# for i in range(0,len(strainsToPlot),4):
#     printTimeCourseOD(replicateExperimentObjectList, strainsToPlot[i:i+3])
#     plt.show()
