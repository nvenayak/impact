__author__ = 'Naveen'
from dataImportandPlottingToolbox.DataObject import *


def getTiterObjectListFromTimePointCollection(timePointCollection):
    titerObjectList = dict()
    for timePoint in timePointCollection:
        flag = 0
        for titerObjectKey in titerObjectList:
            if timePoint[list(timePoint.keys())[0]].getUniqueTimePointID() == \
                    titerObjectList[titerObjectKey][list(timePoint.keys())[0]].getTimeCourseID():
                    ##TODO We can check only one key since they should all be the same, this will be checked later
                for key in titerObjectList[titerObjectKey]:
                    titerObjectList[titerObjectKey][key].addTimePoint(timePoint[key])
                flag = 1
                break
        if flag == 0:
            titerObjectList[timePoint[list(timePoint.keys())[0]].getUniqueTimePointID()] = dict()
            for key in timePoint:
                titerObjectList[timePoint[key].getUniqueTimePointID()][key] = timeCourseObject()
                titerObjectList[timePoint[key].getUniqueTimePointID()][key].addTimePoint(timePoint[key])
    return titerObjectList

# ----------------- Deprecated ------------------ #
# def getSingleExperimentObjectListFromTiterObjectList(titerObjectList, substrateName, titerODFlag):
#     singleExperimentObjectList = dict()
#     if titerODFlag=='titer':
#         for key in titerObjectList: #Go through each titerObjectList
#             singleExperimentObjectList[key] = SingleTrial()
#             for key2 in titerObjectList[key]:
#                 #print(titerObjectList[key][key2].RunIdentifier.returnUniqueID_singleExperiment())
#                 singleExperimentObjectList[key].addTiterObject(titerObjectList[key][key2])
#                 # if key2 == substrateName:
#                 #     singleExperimentObjectList[key].substrate = titerObjectList[key][key2]
#                 # else:
#                 #     singleExperimentObjectList[key].setProduct(key2, titerObjectList[key][key2])
#     elif titerODFlag == 'OD':
#         for key in titerObjectList:
#             singleExperimentObjectList[key] = SingleTrial()
#             singleExperimentObjectList[key].addTiterObject(titerObjectList[key])
#     else:
#         raise Exception("No titer/OD flag set")
#     return singleExperimentObjectList
#
# def getReplicateExperimentObjectListFromSingleExperimentObjectList(singleExperimentObjectList):
#     replicateExperimentObjectList = dict()
#     for key in singleExperimentObjectList:
#         flag = 0
#         for key2 in replicateExperimentObjectList:
#             #print(key2, singleExperimentObjectList[key].getUniqueReplicateID())
#             if key2 == singleExperimentObjectList[key].getUniqueReplicateID():
#                 #print("Replicate found")
#                 replicateExperimentObjectList[key2].addReplicateExperiment(singleExperimentObjectList[key])
#                 flag = 1
#                 break
#         if flag == 0:
#             replicateExperimentObjectList[singleExperimentObjectList[key].getUniqueReplicateID()] = ReplicateTrial()
#             tempID = singleExperimentObjectList[key].getUniqueReplicateID()
#             replicateExperimentObjectList[singleExperimentObjectList[key].getUniqueReplicateID()].addReplicateExperiment(singleExperimentObjectList[key])
#     return replicateExperimentObjectList