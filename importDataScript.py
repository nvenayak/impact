__author__ = 'Naveen'

####### Import packages
from DataObject import *
from pyexcel_xlsx import get_data

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
singleExperimentDataList = []
skippedLines = 0

######## Parse the titer data into single experiment object list
for i in range(6, len(data['titers'])):
    if type("asdf") == type(data['titers'][i][0]):  #Check if the data is a string
        tempParsedIdentifier = data['titers'][i][0].split(',')  #Parse the string using comma delimiter
        if len(tempParsedIdentifier) >= 3:  #Ensure corect number of identifiers TODO make this general
            tempRunIdentifierObject = runIdentifier()
            tempRunIdentifierObject.strainID = tempParsedIdentifier[0]
            #tempRunIdentifierObject.identifier1 = tempParsedIdentifier[1]
            # tempRunIdentifierObject.identifier2 = tempParsedIdentifier[2]
            tempRunIdentifierObject.replicate = tempParsedIdentifier[1]
            tempRunIdentifierObject.t = tempParsedIdentifier[2]

            singleExperimentDataList.append(singleExperimentData())
            for key in tempTimePointCollection:
                tempTimePointCollection[key] = timePoint(tempRunIdentifierObject, key, tempRunIdentifierObject.time, data['titers'][i][titerNameColumn[key]])
                if key == substrateName:
                    print(tempTimePointCollection[key])
                    singleExperimentDataList[-1].substrate = tempTimePointCollection[key]
                else:
                    singleExperimentDataList[-1].products[key] = tempTimePointCollection[key]

            timePointCollection.append(tempTimePointCollection.copy())
        else:
            skippedLines = skippedLines + 1
    else:
        skippedLines = skippedLines+1
print("Number of lines skipped ",skippedLines)


######## Combine replicate experiments
uniqueTimePointCollection = dict()
#Find unique timePointIdentifiers
for i in singleExperimentDataList:
    if i.getUniqueTimePointID() in uniqueTimePointCollection:
        uniqueTimePointCollection[i.getUniqueTimePointID()].append(i)
    else:
        uniqueTimePointCollection[i.getUniqueTimePointID()] = [i]

######### Build the replicate objects
replicateExperimentObjectList = dict()
replicateExperimentObject()

for key in uniqueTimePointCollection.keys():
    replicateExperimentObjectList[key] = replicateExperimentObject()
    for i in uniqueTimePointCollection[key]:
        replicateExperimentObjectList[key].addReplicateExperiment(i)