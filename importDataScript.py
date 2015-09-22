__author__ = 'Naveen'

import DataObject

t = np.array([0,2.5,4,6,9,12,14,17,20,23])
data = np.array([0.0633166666666667,0.107116668166667,0.126316665500000,0.162466665000000,0.254633329833333,0.290883332500000,0.305849996666667,0.311133335000000,0.312383334000000,0.318266670000000])

dataObjectTest = timeCourseObject(t, data)
print(dataObjectTest.productionRate)



from pyexcel_xlsx import get_data

#Data must be in the following format:
#Sheet name: OD, col 1: names, col2:
#Sheet name: titers



for key in data.keys():
    print data.get(key)
for key, elem in data.items():
    print key, elem
for i in data:
     print i, data[i]
for key in data.iterkeys():
    print(key, data[key])
for c in a:
    print(c)


data = get_data("test1.xlsx")
data['Sheet1'].split(",")
for key in data.keys():
    print(data[key])
#Import the data

#Go through the names array
    #Parse the information: Strain ID, Identifier1 (Plasmid), Identifier2, condition
    #Check if singleExperimentData exists for the dataType
        #if yes, add to singleExperimentData

        #if no, make a new singleExperimentData object
from pyexcel_xlsx import get_data

data = get_data("test1.xlsx")
if 'OD' not in data.keys():
    raise Exception("No sheet named 'OD' found")

if 'titers' not in data.keys():
    raise Exception("No sheet named 'titers' found")

for i in range(0, len(data['OD'])):
    #Parse the identifier
    tempParsedIdentifier = data['OD'][i][0].split(','))
    tempRunIdentifierObject = runIdentifier
    tempRunIdentifierObject.strainID = tempParsedIdentifier[0]
    tempRunIdentifierObject.identifier1 = tempParsedIdentifier[1]
    tempRunIdentifierObject.identifier2 = tempParsedIdentifier[2]
    tempRunIdentifierObject.replicate = tempParsedIdentifier[3]
    #ODs[i][0].time = tempParsedIdentifier[4]

    timeCourseObjectList[i] = timeCourseObject(tempParsedIdentifier,data['ODt'][0],data['OD'][i][1:len(data['OD'][i])])

#Loop through each timeCourseObject
for i in range(1:len(timeCourseObjectList)
    #Loop through all the experimentObjects to check if one with the same conditions exists
    for j in 1:len(replicateObjectList)
        if timeCourseObjectList[i].runIdentifier.strainID == replicateObjectList.runIdentifier.strainID and #check identifier 1 and 2

if 'Sheetx' in data.keys():
    print("yes")
else:
    print("no")