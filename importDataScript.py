__author__ = 'Naveen'

####### Import packages
from DataObject import *
from pyexcel_xlsx import get_data
from dataParsingFunctions import *
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
titerObjectList = getTiterObjectListFromTimePointCollection(timePointCollection)

######## Combine timeCourseObjects into singleExperimentObjects
singleExperimentObjectList = getSingleExperimentObjectListFromTiterObjectList(titerObjectList, substrateName)

######## Combine singleExperimentObjects into replicateExperimentObjects
replicateExperimentObjectList = getReplicateExperimentObjectListFromSingleExperimentObjectList(singleExperimentObjectList)



#def plotYields():
handle = dict()
barWidth = 0.1
location = 0
# print(replicateExperimentObjectList[key].t)
# print(replicateExperimentObjectList[key].avg.yields["Ethanol"])
# print(replicateExperimentObjectList[key].std.yields["Ethanol"])

inputVal = "Y"
for key in replicateExperimentObjectList:
    print("Experiment name: ",key)
    #rects = plt.bar(replicateExperimentObjectList[key].t+location,replicateExperimentObjectList[key].avg.yields["Ethanol"],barWidth,yerr=replicateExperimentObjectList[key].std.yields["Ethanol"])#,lw=2.5,elinewidth=1,capsize=2)#,fmt='o-')

    inputVal = input("Include sample?")
    #rects = plt.bar(replicateExperimentObjectList[key].t+location,replicateExperimentObjectList[key].avg.yields["Ethanol"],barWidth,yerr=replicateExperimentObjectList[key].std.yields["Ethanol"])#,lw=2.5,elinewidth=1,capsize=2)#,fmt='o-')

    if inputVal == "Y":
    # print("t: ",replicateExperimentObjectList[key].t)
    # print("avg: ",replicateExperimentObjectList[key].avg.yields)
    # print("std: ",replicateExperimentObjectList[key].std.yields["Ethanol"])
        rects = plt.bar(replicateExperimentObjectList[key].t+location,replicateExperimentObjectList[key].avg.yields["Ethanol"],barWidth,yerr=replicateExperimentObjectList[key].std.yields["Ethanol"])#,lw=2.5,elinewidth=1,capsize=2)#,fmt='o-')
        location += barWidth

    # rects = plt.bar(replicateExperimentObjectList[key].t+location,replicateExperimentObjectList[key].avg.yields["Ethanol"],barWidth,yerr=replicateExperimentObjectList[key].std.yields["Ethanol"])#,lw=2.5,elinewidth=1,capsize=2)#,fmt='o-')
    # location += barWidth
plt.legend([handle[key] for key in handle],[key for key in handle])
plt.ylim([0,0.3])


# You typically want your plot to be ~1.33x wider than tall. This plot is a rare
# exception because of the number of lines being plotted on it.
# Common sizes: (10, 7.5) and (12, 9)
plt.figure(figsize=(12, 14))

# Remove the plot frame lines. They are unnecessary chartjunk.
ax = plt.subplot(111)


ax.spines["top"].set_visible(False)
ax.spines["bottom"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)


handle = dict()
for key in replicateExperimentObjectList:
    handle[key] = plt.errorbar(replicateExperimentObjectList[key].t,replicateExperimentObjectList[key].avg.products["Ethanol"],replicateExperimentObjectList[key].std.products["Ethanol"],lw=2.5,elinewidth=1,capsize=2,fmt='o-')
plt.legend([handle[key] for key in handle],[key for key in handle])

