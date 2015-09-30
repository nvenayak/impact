__author__ = 'Naveen Venayak'

import numpy as np
import scipy.optimize as opt

class runIdentifier(object):
    #Base runIdentifier object
    def __init__(self):
        self.strainID = ''
        self.identifier1 = ''
        self.identifier2 = ''
        self.replicate = None
        self.time = None

    def returnUniqueID(self):
        return self.strainID+self.identifier1+self.identifier2

class timePoint(object):
    def __init__(self, runID, titerName, t, titer):
        self.runIdentifier = runID
        self.titerName = titerName
        self. t = t
        self.titer = titer

    def getUniqueTimePointID(self):
        return self.runIdentifier.strainID+self.runIdentifier.identifier1+self.runIdentifier.identifier2+str(self.runIdentifier.replicate)

class titerObject():
    #def __init__(self, runID, prodID, t, data):
    def __init__(self):
        self.timePointList = []

    def addTimePoint(self, timePoint):
        raise(Exception("No addTimePoint method defiend in the child"))

    def getTimeCourseID(self):
        return self.timePointList[0].runIdentifier.strainID+\
               self.timePointList[0].runIdentifier.identifier1+\
               self.timePointList[0].runIdentifier.identifier2+\
               str(self.timePointList[0].runIdentifier.replicate)

    def getReplicateID(self):
        return self.timePointList[0].runIdentifier.strainID+self.timePointList[0].runIdentifier.identifier1+self.timePointList[0].runIdentifier.identifier2

class timeCourseObject(titerObject):
    #Object contains one time vector and one data vector
    def __init__(self):
        titerObject.__init__(self)
        self.timeVec = None
        self.dataVec = None

    def addTimePoint(self, timePoint):
        self.timePointList.append(timePoint)
        self.timePointList.sort(key=lambda timePoint: timePoint.t)
        self.timeVec = np.array([timePoint.t for timePoint in self.timePointList])
        self.dataVec = np.array([timePoint.titer for timePoint in self.timePointList])
        #print(self.timeVec)

    def calcExponentialRate(self, t, data):
        #Define the growth equation to fit parameters
        def growthEquation(t, X0, K, mu):
            return X0*K/(X0+ (K-X0)*np.exp(-mu*t))
        #Fit and return the parameters
        popt, pcov = opt.curve_fit(growthEquation,t,data)
        return popt

class endPointObject(titerObject):
    def __init__(self, runID, t, data):
        titerObject.__init__(self, runID, t, data)
        #self.data = data
        #self.runID = runID
    def addTimePoint(self, timePoint):
        if len(self.timePointList) < 2:
            self.timePointList.append(timePoint)
        else:
            raise(Exception("Cannot have more than two timePoints for an endPoint Object"))

        if len(self.timePointList) == 2:
            self.timePointList.sort(key=lambda timePoint: timePoint.t)

class productsObject(object):
    def __init__(self, names, timeCourses):
        self.names = names
        self.timeCourses = timeCourses


class singleExperimentData(object):
    #Object contains a series of timeCourseObjects related to a single experiment
    def __init__(self):
        self.__t = np.array([])
        self.__OD = []
        self.__substrate = []
        self.products = dict()
        #self.yields = self.calcYield()
        #self.substrateConsumed = self.calcSubstrateConsumed()

    @property
    def OD(self):
        return self.__OD

    @OD.setter
    def OD(self, OD):
        self.__OD = OD
        self.checkTimeVectors()

    @property
    def substrate(self):
        return self.__substrate

    @substrate.setter
    def substrate(self, substrate):
        self.__substrate = substrate
        self.checkTimeVectors()

    @property
    def t(self):
        return self.__t

    @t.setter
    def t(self, t):
        self.__t = t

    # @property
    # def products(self):
    #     return self.__products
    #
    # @products.setter
    # def products(self, products):
    #     self.__products = products

    def checkTimeVectors(self):
        t = []
        flag = 0
        if self.OD:
            t.append(self.OD.timeVec)
        if self.substrate != None:
            try:
                t.append(self.substrate.timeVec)
            except:
                a = 0

        if self.products:
            for key in self.products:
                t.append(self.products[key].timeVec)

        for i in range(len(t)-1):
            #print(t[i])
            if (t[i] != t[i+1]).all():
                flag = 1


        if flag==1:
            raise(Exception("Time vectors within an experiment don't match, must implement new methods to deal with this type of data (if even possible)"))
        else:
            self.__t = self.substrate.timeVec

    def getUniqueTimePointID(self):
        return self.substrate.runIdentifier.strainID+self.substrate.runIdentifier.identifier1+self.substrate.runIdentifier.identifier2+str(self.substrate.runIdentifier.replicate)

    def getUniqueReplicateID(self):
        return self.substrate.getReplicateID()

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


class singleExperimentDataShell(singleExperimentData):
    # def __init__(self):
    #     replicateExperimentObject.__init__(self)

    @singleExperimentData.substrate.setter
    def substrate(self, substrate):
        self.__substrate = substrate

    @singleExperimentData.OD.setter
    def OD(self, OD):
        self.__OD = OD

    # @singleExperimentData.products.setter
    # def products(self, products):
    #     self.__products = products




class replicateExperimentObject(object):
    #Calculates statistics based on replicates
    def __init__(self):
        self.avg = singleExperimentDataShell()
        self.std = singleExperimentDataShell()
        self.t = None
        self.singleExperimentList = []
        #self.useReplicate = dict()
        #self.checkReplicateUniqueIDMatch()

    def checkReplicateUniqueIDMatch(self):
        for i in range(len(self.singleExperimentList)-1):
            if self.singleExperimentList[i].getUniqueReplicateID() != self.singleExperimentList[i+1].getUniqueReplicateID():
                raise(Exception("the replicates do not have the same uniqueID, either the uniqueID includes too much information or the strains don't match"))

            if (self.singleExperimentList[i].t != self.singleExperimentList[i+1].t).all():
                raise(Exception("time vectors don't match within replicates"))
            else:
                self.t = self.singleExperimentList[i].t

            if len(self.singleExperimentList[i].substrate.dataVec) != len(self.singleExperimentList[i+1].substrate.dataVec):
                print("Time Vector 1: ",self.singleExperimentList[i].t,"\nTime Vector 2: ",self.singleExperimentList[i+1].t)
                print("Vector 1: ",self.singleExperimentList[i].substrate.dataVec,"\nVector 2: ",self.singleExperimentList[i+1].substrate.dataVec)
                raise(Exception("length of substrate vectors do not match"))

            for key in self.singleExperimentList[i].products:
                if len(self.singleExperimentList[i].products[key].dataVec) != len(self.singleExperimentList[i+1].products[key].dataVec):
                    raise(Exception("length of product vector "+str(key)+" do not match"))

    def addReplicateExperiment(self, newReplicateExperiment):
        self.singleExperimentList.append(newReplicateExperiment)
        self.checkReplicateUniqueIDMatch()
        self.calcAverageAndDev()

    #Calculate averages
    def calcAverageAndDev(self):
        #First check what data exists
        ODflag = 0
        productFlag = 0
        substrateFlag = 0
        for singleExperiment in self.singleExperimentList:
            # TODO timePoint,
            if singleExperiment.OD:
                temp=0
            if singleExperiment.products:
                productFlag = 1 #TODO need to make generic for different products in different expts
            if singleExperiment.substrate:
                substrateFlag=1

        if ODflag == 1:
            self.avg.OD = np.mean([singleExperimentObject.OD.dataVec for singleExperimentObject in self.singleExperimentList], axis=0)
            self.std.OD = np.std([singleExperimentObject.OD.dataVec for singleExperimentObject in self.singleExperimentList], axis=0)

        if productFlag == 1:
            for key in self.singleExperimentList[0].products:
                # for singleExperimentObject in self.singleExperimentList:
                #     for timePoint in singleExperimentObject.products[key].timePointList:
                #             print(timePoint.getUniqueTimePointID())
                #

                # print("Next: ",[singleExperimentObject.products[key].timeVec for singleExperimentObject in self.singleExperimentList])

                self.avg.products[key] = np.mean([singleExperimentObject.products[key].dataVec for singleExperimentObject in self.singleExperimentList],axis=0)
                self.std.products[key] = np.std([singleExperimentObject.products[key].dataVec for singleExperimentObject in self.singleExperimentList],axis=0)

        if substrateFlag == 1:
            # for singleExperimentObject in self.singleExperimentList:
            #         for timePoint in singleExperimentObject.substrate.timePointList:
            #                 print(timePoint.getUniqueTimePointID())
            #
            # print("substrateNext: ",[singleExperimentObject.substrate.dataVec for singleExperimentObject in self.singleExperimentList])

            self.avg.substrate = np.mean([singleExperimentObject.substrate.dataVec for singleExperimentObject in self.singleExperimentList], axis=0)
            self.std.substrate = np.std([singleExperimentObject.substrate.dataVec for singleExperimentObject in self.singleExperimentList], axis=0)



    #Calculate the production rate average

    #Calculate the growth rate average


