__author__ = 'Naveen Venayak'

import numpy as np
import scipy.optimize as opt

class runIdentifier(object):

    strainID = ''
    identifier1 = ''
    identifier2 = ''
    replicate = 0
    time = 0

    def returnUniqueID(self):
        return self.strainID+self.identifier1+self.identifier2

class timePoint(object):
    def __init__(self, runID, titerName, t, titer):
        self.runIdentifier = runID
        self.titerName = titerName
        self. t = t
        self.titer = titer

    def getUniqueTimePointID(self):
        return self.runIdentifier.strainID+self.runIdentifier.identifier1+self.runIdentifier.identifier2+self.runIdentifier.replicate

class titerData():
    def __init__(self, runID, prodID, t, data):
        self.t = t
        self.prodID = prodID
        self.data = data
        self.runID = runID

class timeCourseObject(titerData):
    #Object contains one time vector and one data vector
    def __init__(self, runID, prodID, t, data):
        titerData.__init__(self, runID, prodID, t, data)
        self.exponentialRate = self.calcExponentialRate(t, data)

    def calcExponentialRate(self, t, data):
        #Define the growth equation to fit parameters
        def growthEquation(t, X0, K, mu):
            return X0*K/(X0+ (K-X0)*np.exp(-mu*t))
        #Fit and return the parameters
        popt, pcov = opt.curve_fit(growthEquation,t,data)
        return popt

class endPointObject(titerData):
    def __init__(self, runID, t, data):
        titerData.__init__(self, runID, t, data)
        #self.data = data
        #self.runID = runID

class productsObject(object):
    def __init__(self, names, timeCourses):
        self.names = names
        self.timeCourses = timeCourses


class singleExperimentData(object):
    #Object contains a series of timeCourseObjects related to a single experiment
    def __init__(self):
        # self.productNames = ['succinate','formate','acetate','ethanol','lactate']
        self.OD = []
        self.substrate = []
        #self.substrateConsumed = self.calcSubstrateConsumed()
        self.products = dict()
        #self.yields = self.calcYield()

    def getUniqueTimePointID(self):
        return self.substrate.runIdentifier.strainID+self.substrate.runIdentifier.identifier1+self.substrate.runIdentifier.identifier2+self.substrate.runIdentifier.replicate

    def calcSubstrateConsumed(self):
        substrateConsumed = []
        for timePoint in range(1,len(self.substrate.titer)):
            substrateConsumed[timePoint] = self.substrate.titer[0]-self.substrate.titer[timePoint]
        return substrateConsumed

    def calcYield(self):
        yields=np.zeros(5,len(self.substrateConsumed)-1)

        for productIndex in len(self.products):
            yields[productIndex,:] = np.divide(self.products.data[productIndex,1:len(self.products)],self.substrateConsumed.data[1:len(self.substrateConsumed)])
        return yields

class replicateExperimentObject(object):
    #Calculates statistics based on replicates
    def __init__(self):
        #self.replicates = replicates
        #self.replicatesToUse = replicatesToUse
        #self.uniqueID = replicates.returnUniqueID()
        self._timeCourseObjectList = []
        #self.yieldAverages, self.titerAverages, self.ODaverages, self.growthRateAverage = calcAverages()
        self.checkReplicateUniqueIDMatch()

    def checkReplicateUniqueIDMatch(self):
        for i in range(len(self.timeCourseObjectList)):
            if self.replicates[i].returnUniqueID() != self.replicates[i].returnUniqueID():
                raise(Exception,"the replicates do not have the same uniqueID, either the uniqueID includes too much information or the strains don't match")


    def addReplicateExperiment(self, newReplicateExperiment):
        self.timeCourseObjectList.append(newReplicateExperiment)
        checkReplicateUniqueIDMatch(self)
        calcAverageandDev(self)

    #Calculate averages
    def calcAveragesAndDev(self, data):
        # TODO timePoint,
        avg = np.mean(replicates.yields[replicatesToUse,])
        std = np.std(replicates.yields[replicatesToUse,])
        return avg, std

    #Calculate the production rate average

    #Calculate the growth rate average


