__author__ = 'Naveen'

from DataObject import *

from pyexcel_xlsx import get_data

#data = get_data("test1.xlsx")
data = get_data("2015.05.19.LactateStoryData.xlsx")

# if 'OD' not in data.keys():
#     raise Exception("No sheet named 'OD' found")

if 'titers' not in data.keys():
    raise Exception("No sheet named 'titers' found")

substrate = "Glucose"
titerDataSheetName = "titers"

titerNameColumn = dict()
for i in range(1,len(data[titerDataSheetName][2])):
    titerNameColumn[data[titerDataSheetName][2][i]] = i


#Build time point objects from titer HPLC data
#timePointCollection = [ [] for i in range(0,len(titerName))]

timePointCollection = dict()
for names in titerNameColumn:
    print(type(names))
    timePointCollection[names] = []


skippedLines = 0
for i in range(6, len(data['titers'])):
    #print(i)
    #Parse the identifier
    if type("asdf") == type(data['titers'][i][0]):
        tempParsedIdentifier = data['titers'][i][0].split(',')
        if len(tempParsedIdentifier) >= 3:
            if len(tempParsedIdentifier) == 3:
                tempRunIdentifierObject = runIdentifier()
                tempRunIdentifierObject.strainID = tempParsedIdentifier[0]
                #tempRunIdentifierObject.identifier1 = tempParsedIdentifier[1]
                # tempRunIdentifierObject.identifier2 = tempParsedIdentifier[2]
                tempRunIdentifierObject.replicate = tempParsedIdentifier[1]
                tempRunIdentifierObject.t = tempParsedIdentifier[2]
                print(tempRunIdentifierObject.returnUniqueID())
        else:
            skippedLines = skippedLines + 1
            #print(tempRunIdentifierObject.t)

        for key in timePointCollection:
            print("the key is",key)
            timePointCollection[key].append(timePoint(tempRunIdentifierObject, key, tempRunIdentifierObject.time, data['titers'][i][titerNameColumn[key]]))
    else:
        skippedLines = skippedLines+1
#Combine the time point objects into timeCourseObject and add to experimentObjects
   # for i in range(0,len(timePointCollection)):
   #      uniqueExperiments.append = timePointCollection[i].runIdentifier.returnUniqueID()
print("Number of lines skipped ",skippedLines )


#uniqueTimePointCollection = [ [] for i in range(len(titerName))]
uniqueTimePointCollection = []
uniqueTimePointCollection.append( dict())

for key in titerNameColumn:
    uniqueTimePointCollection[0][key] = []

for i in range(0,len(timePointCollection['Glucose'])): #### Should be generalized
    #Loop through all the experimentObjects to check if one with the same conditions exists
    flag = 0
    for j in range(0,len(uniqueTimePointCollection['Glucose'])):
        if uniqueTimePointCollection['Glucose'][j].getUniqueTimePointID() == timePointCollection['Glucose'][i].getUniqueTimePointID():
            for key in timePointCollection:
                uniqueTimePointCollection[key][j].append(timePointCollection[key][i])
            flag = 1
            print("flag is 1")
            break
    if flag == 0:
        for key in timePointCollection:
            #print(i," "," ",key)
            print("flag is 0")
            uniqueTimePointCollection[key].append(timePointCollection[key][i])
        #print(uniqueTimePointCollection[0][i].runIdentifier.strainID)












# for i in range(5,len(uniqueTimePointCollection)):
#     print(uniqueTimePointCollection[i].getUniqueTimePointID())
#
# for i in range(0, len(data['OD'])):
#     #Parse the identifier
#     tempParsedIdentifier = data['OD'][i][0].split(',')
#     tempRunIdentifierObject = runIdentifier
#     tempRunIdentifierObject.strainID = tempParsedIdentifier[0]
#     tempRunIdentifierObject.identifier1 = tempParsedIdentifier[1]
#     tempRunIdentifierObject.identifier2 = tempParsedIdentifier[2]
#     tempRunIdentifierObject.replicate = tempParsedIdentifier[3]
#     #ODs[i][0].time = tempParsedIdentifier[4]
#
#     timeCourseObjectList[i] = timeCourseObject(tempParsedIdentifier,data['ODt'][0],data['OD'][i][1:len(data['OD'][i])])
#
# replicateObjectList = []
#
#
#
#
#
# #Loop through each timeCourseObject
# for i in len(timeCourseObjectList):
#     #Loop through all the experimentObjects to check if one with the same conditions exists
#     flag = 0
#     for j in len(replicateObjectList):
#         if timeCourseObjectList[i].runIdentifier.returnUniqueID() == replicateObjectList[j].runIdentifier.returnUniqueID():
#             replicateObjectList[j].addReplicateExperiment(timeCourseObjectList[i])
#             flag = 1
#             break
#     if flag == 0:
#         replicateObjectList.append(timeCourseObjectList[i])




#
#
#
#
#
#
#
#
#
#
# #Miscellaneous
# t = np.array([0,2.5,4,6,9,12,14,17,20,23])
# data = np.array([0.0633166666666667,0.107116668166667,0.126316665500000,0.162466665000000,0.254633329833333,0.290883332500000,0.305849996666667,0.311133335000000,0.312383334000000,0.318266670000000])
#
# dataObjectTest = timeCourseObject(runIdentifier(), t, data)
# print(dataObjectTest.exponentialRate)
#
#
#
# from pyexcel_xlsx import get_data
#
# #Data must be in the following format:
# #Sheet name: OD, col 1: names, col2:
# #Sheet name: titers
#
#
#
# for key in data.keys():
#     print data.get(key)
# for key, elem in data.items():
#     print key, elem
# for i in data:
#      print i, data[i]
# for key in data.iterkeys():
#     print(key, data[key])
# for c in a:
#     print(c)
#
#
# data = get_data("test1.xlsx")
# data['Sheet1'].split(",")
# for key in data.keys():
#     print(data[key])
# # Import the data
#
# #Go through the names array
#     #Parse the information: Strain ID, Identifier1 (Plasmid), Identifier2, condition
#     #Check if singleExperimentData exists for the dataType
#         #if yes, add to singleExperimentData
#
#         #if no, make a new singleExperimentData object
#
#
#
#
#
#
# if 'Sheetx' in data.keys():
#     print("yes")
# else:
#     print("no")