__author__ = 'Naveen'

####### Import packages
from DataObject import *
from pyexcel_xlsx import get_data
import matplotlib.pyplot as plt

####### Define some constants
fileName = "2015.05.19.LactateStoryData.xlsx"
substrateName = 'Glucose'
titerDataSheetName = "titers"


###############################

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
for i in range(4, len(data['titers'])):
    if type("asdf") == type(data['titers'][i][0]):  #Check if the data is a string
        tempParsedIdentifier = data['titers'][i][0].split(',')  #Parse the string using comma delimiter
        if len(tempParsedIdentifier) >= 3:  #Ensure corect number of identifiers TODO make this general
            tempRunIdentifierObject = runIdentifier()
            tempRunIdentifierObject.strainID = tempParsedIdentifier[0]
            #tempRunIdentifierObject.identifier1 = tempParsedIdentifier[1]
            # tempRunIdentifierObject.identifier2 = tempParsedIdentifier[2]
            tempParsedReplicate = tempParsedIdentifier[1].split('=')
            tempRunIdentifierObject.replicate = int(tempParsedReplicate[1])#tempParsedIdentifier[1]
            tempParsedTime = tempParsedIdentifier[2].split('=')
            tempRunIdentifierObject.t = float(tempParsedTime[1])#tempParsedIdentifier[2]
            for key in tempTimePointCollection:
                tempTimePointCollection[key] = timePoint(tempRunIdentifierObject, key, tempRunIdentifierObject.t, data['titers'][i][titerNameColumn[key]])
            timePointCollection.append(tempTimePointCollection.copy())
        else:
            skippedLines += 1
    else:
        skippedLines += 1

print("Number of lines skipped ",skippedLines)

######## Combine time points into timeCourseObjects
titerObjectList = dict()
for timePoint in timePointCollection:
    flag = 0
    for titerObjectKey in titerObjectList:
        if timePoint["Glucose"].getUniqueTimePointID() == titerObjectList[titerObjectKey]["Glucose"].getTimeCourseID(): ##We can check only one key since they should all be the same, this will be checked later
            for key in titerObjectList[titerObjectKey]:
                titerObjectList[titerObjectKey][key].addTimePoint(timePoint[key])
            flag = 1
            break
    if flag == 0:
        titerObjectList[timePoint[key].getUniqueTimePointID()] = dict()
        for key in timePoint:
            titerObjectList[timePoint[key].getUniqueTimePointID()][key] = timeCourseObject()
            titerObjectList[timePoint[key].getUniqueTimePointID()][key].addTimePoint(timePoint[key])
    # for x in titerObjectList[timePoint[key].getUniqueTimePointID()][key].timePointList:
    #     print(x.t)

# for key in titerObjectList:
#     print(titerObjectList[key]["Glucose"].timeVec)

######## Combine timeCourseObjects into singleExperimentObjects
singleExperimentObjectList = dict()
for key in titerObjectList:
    singleExperimentObjectList[key] = singleExperimentData()
    for key2 in titerObjectList[key]:
        if key2 == substrateName:
            singleExperimentObjectList[key].substrate = titerObjectList[key][key2]
        else:
            singleExperimentObjectList[key].products[key2] = titerObjectList[key][key2]
            #print(type(singleExperimentObjectList[key].products[key2]))


######## Combine singleExperimentObjects into replicateExperimentObjects
replicateExperimentObjectList = dict()
for key in singleExperimentObjectList:
    flag = 0
    for key2 in replicateExperimentObjectList:
        if key2 == singleExperimentObjectList[key].getUniqueReplicateID():
            replicateExperimentObjectList[key2].addReplicateExperiment(singleExperimentObjectList[key])
            flag = 1
            break
    if flag == 0:
        replicateExperimentObjectList[singleExperimentObjectList[key].getUniqueReplicateID()] = replicateExperimentObject()
        tempID = singleExperimentObjectList[key].getUniqueReplicateID()
        replicateExperimentObjectList[singleExperimentObjectList[key].getUniqueReplicateID()].addReplicateExperiment(singleExperimentObjectList[key])

for key in replicateExperimentObjectList:#
    print(replicateExperimentObjectList[key].avg.products["Ethanol"])
    print(replicateExperimentObjectList[key].t)
    print(len(replicateExperimentObjectList[key].t),len(replicateExperimentObjectList[key].avg.products["Ethanol"]))
    plt.plot(replicateExperimentObjectList[key].t,replicateExperimentObjectList[key].avg.products["Ethanol"])

