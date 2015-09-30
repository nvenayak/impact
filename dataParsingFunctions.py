__author__ = 'Naveen'
######## Combine time points into timeCourseObjects
titerObjectList = getTiterObjectListFromTimePointCollection(timePointCollection)

######## Combine timeCourseObjects into singleExperimentObjects
singleExperimentObjectList = getSingleExperimentObjectListFromTiterObjectList(titerObjectList)

######## Combine singleExperimentObjects into replicateExperimentObjects
replicateExperimentObjectList = getReplicateExperimentObjectListFromSingleExperimentObjectList(singleExperimentObjectList)

def getTiterObjectListFromTimePointCollection(timePointCollection):
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
            titerObjectList[timePoint[[list(timePoint.keys())[0]].getUniqueTimePointID()] = dict()
            for key in timePoint:
                titerObjectList[timePoint[key].getUniqueTimePointID()][key] = timeCourseObject()
                titerObjectList[timePoint[key].getUniqueTimePointID()][key].addTimePoint(timePoint[key])
    return titerObjectList

def getSingleExperimentObjectListFromTiterObjectList(titerObjectList):
    singleExperimentObjectList = dict()
    for key in titerObjectList:
        singleExperimentObjectList[key] = singleExperimentData()
        for key2 in titerObjectList[key]:
            if key2 == substrateName:
                singleExperimentObjectList[key].substrate = titerObjectList[key][key2]
            else:
                singleExperimentObjectList[key].setProduct(key2, titerObjectList[key][key2])
    return singleExperimentObjectList

def getReplicateExperimentObjectListFromSingleExperimentObjectList(singleExperimentObjectList):
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
    return replicateExperimentObjectList