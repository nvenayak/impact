'''
Written by: Naveen Venyak
Date:       October, 2015

This file will parse data in standard 'NV_OD' format and output plots of the data
'''


# Define some constants
rawDataFileName = "rawData/2015.10.08 pTOG Automation Test.xlsx"
saveFileName = 'pickledData/parseGrowthCurvesPickle.p'
dataFormat = 'NV_OD'
p1 = True  # True to re-parse data, False to load data

# Import packages
from DataObject import *

# Build the data object
newProjectContainer = projectContainer()
if p1 == True:
    # Add the data to the project
    newProjectContainer.parseRawData(rawDataFileName, dataFormat)

    # Pickles the object
    newProjectContainer.pickle(saveFileName)
else:
    # Unpickles the object
    newProjectContainer.unpickle(saveFileName)

# Choose strains to plot
strainsToPlot = ['3KO-D1pTOG009IPTG','3KO-D1pTOG009aTc','3KO-D30pTOG009IPTG','3KO-D30pTOG009aTc','3KO-D1pTOG010IPTG','3KO-D1pTOG010aTc','3KO-D30pTOG010IPTG','3KO-D30pTOG010aTc']

# Plot growth rate bar chart
sortBy = 'identifier2'  # for sortBy in ['strainID','identifier1','identifier2']:
newProjectContainer.printGrowthRateBarChart(strainsToPlot, sortBy)

# Plot the time course of all strains
newProjectContainer.printGenericTimeCourse(titersToPlot=['OD'])

# Show all the plots
plt.show()