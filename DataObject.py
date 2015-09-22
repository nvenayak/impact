__author__ = 'Naveen Venayak'

import numpy as np
import scipy.optimize as opt

class timeCourseObject(object):
    #Object contains one time vector and one data vector

    def __init__(self, strainID, t, data):
        self.t = t;
        self.data = data;
        self.productionRate = self.calcProductionRate(t, data);
        self.strainID = strainID;

    def calcExponentialRate(self, t, data):

        def growthEquation(t, X0, K, mu):
            return X0*K/(X0+ (K-X0)*np.exp(-mu*t))

        popt, pcov = opt.curve_fit(growthEquation,t,data)

        return popt

class singleExperimentData(object)
    #Object contains a series of timeCourseObjects related to a single experiment


    def __init__(self, t, OD, glucose, succinate, formate, acetate, ethanol, lactate):
        self.productNames = ['succinate','formate','acetate','ethanol','lactate']

        self.t = t
        self.OD = OD

        self.substrate = glucose
        self.substrateConsumed = self.calcSubstrateConsumed()

        products = np.zeros(5,len(t))

        self.products[1,:] = succinate
        self.products[2,:] = formate
        self.products[3,:] = acetate
        self.products[4,:] = ethanol
        self.products[5,:] = lactate



        #yields = np.zeros(5,len(t))
        self.yields = self.calcYield()

    def calcSubstrateConsumed(self):
        for timePoint in len(self.substrate):
            substrateConsumed = self.substrate[0]-self.substrate[timePoint]
        return substrateConsumed

    def calcYield(self):
        yields=np.zeros(5,len(self.substrateConsumed)-1);
        for productIndex in len(self.products):
            yields[productIndex,:] = np.divide(self.products[productIndex,1:len(self.products)],self.substrateConsumed[1:len(self.substrateConsumed)])

        return yields

class replicateExperimentObject(object)
    #Calculates statistics based on replicates
    def __init__(self, replicates, replicatesToUse):
        self.yieldAverages, self.titerAverages, self.ODaverages, self.growthRateAverage = calcAverages();
    #Calculate the yield average
    def calcAverages(self):
        yieldAverage = np.mean(replicates.yields)
    #Calculate the production rate average

    #Calculate the growth rate average

    $

class runIdentifier(object):
    strainID = ''
    identifier1 = ''
    identifier2 = ''
    replicate = 0
    time = 0






class experimentObject(object)
    def __init__(self, ODtimeCourse,


# class DataObject(object):
#     def __init__(self, t, titers):
#         pass
#
#     def populateDataObject(self, timeCourseObjectList):
#         numTimeCourses = len(timeCourseObjectList)


