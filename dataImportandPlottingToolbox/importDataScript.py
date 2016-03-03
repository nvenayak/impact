__author__ = 'Naveen'

####### Import packages
import pickle
import os

from pyexcel_xlsx import get_data
from DataObject import *

####### Define some constants
fileName = os.path.join(os.path.dirname(__file__),"rawData/2015.05.19.LactateStoryData.xlsx")

saveFileName = 'pickledData/importDataScriptPickle.p'

# # Reparse the data, or load from old pickle?
# loadFromPickle = True
newProjectContainer = projectContainer()
newProjectContainer.parseRawData(fileName,'NV_titers')
# newProjectContainer.unpickle(saveFileName)


# ######## List Experiment names
# print("Experiment Name\t# Replicates\t#Products")
# for key in replicateExperimentObjectList:
#     print(key,"\t\t",len(replicateExperimentObjectList[key].singleExperimentList))


####### Strains To Plot
strainsToPlotList = [['pTOG009IPTG','pTOG009aTc'],['pTOG007IPTG','pTOG007aTc'],['pTOG008IPTG','pTOG08aTc'],['pTOG0010IPTG','pTOG010aTc'],['lacI  pKDL071']]

strainsToPlot = []
for strainsToPlotPair in strainsToPlotList:
    for strainToPlot in strainsToPlotPair:
        strainsToPlot.append(strainToPlot)

# strainsToPlot = ['lacI  pKDL071','pTOG009IPTG','pTOG009aTc']

# newProjectContainer.printGenericTimeCourse(strainsToPlot=strainsToPlot)
# newProjectContainer.printEndPointYield(strainsToPlot, 0)
# plt.show()
# # newProjectContainer.printYieldTimeCourse(strainsToPlot)
# newProjectContainer.printEndPointYield(titersToPlot=['Ethanol','Acetate','Lactate'])
# newProjectContainer.plottingGUI()
