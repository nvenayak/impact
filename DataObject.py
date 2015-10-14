__author__ = 'Naveen Venayak'

import numpy as np
import scipy.optimize as opt
from lmfit import Model
import matplotlib.pyplot as plt

class runIdentifier(object):
    #Base runIdentifier object
    def __init__(self):
        self.strainID = ''
        self.identifier1 = ''
        self.identifier2 = ''
        self.replicate = None
        self.time = None
        self.titerName = 'None'
        self.titerType = 'None'

    def getRunIdentifier(self, row):
        if type("asdf") == type(row):
            tempParsedIdentifier = row.split(',')
            print(tempParsedIdentifier)
            if len(tempParsedIdentifier) == 0:
                print(tempParsedIdentifier," <-- not processed")
            if len(tempParsedIdentifier) > 0 :
                self.strainID = tempParsedIdentifier[0]
            if len(tempParsedIdentifier) > 1 :
                self.identifier1 = tempParsedIdentifier[1]
            if len(tempParsedIdentifier) > 2 :
                self.identifier2 = tempParsedIdentifier[2]
            if len(tempParsedIdentifier) > 3 :
                try:
                    self.replicate = int(tempParsedIdentifier[3])
                except:
                    print("Couldn't parse replicate from ",tempParsedIdentifier)

    def returnUniqueID_singleExperiment(self):
        return self.strainID+self.identifier1+self.identifier1+str(self.replicate)+self.titerName+self.titerType

    def returnUniqueID(self):
        return self.strainID+self.identifier1+self.identifier2

    def returnUniqueExptID(self):
        return self.strainID+self.identifier1+self.identifier2+str(self.replicate)

class timePoint(object):
    def __init__(self, runID, titerName, t, titer):
        self.runIdentifier = runID
        self.titerName = titerName
        self. t = t
        self.titer = titer

    def getUniqueTimePointID(self):
        return self.runIdentifier.strainID+self.runIdentifier.identifier1+self.runIdentifier.identifier2+str(self.runIdentifier.replicate)

class titerObject():
    def __init__(self):
        self.timePointList = []
        self.runIdentifier = runIdentifier()

    def addTimePoint(self, timePoint):
        raise(Exception("No addTimePoint method defiend in the child"))

    def getTimeCourseID(self):
        if len(self.timePointList)>0:
            return self.timePointList[0].runIdentifier.strainID+\
                   self.timePointList[0].runIdentifier.identifier1+\
                   self.timePointList[0].runIdentifier.identifier2+\
                   str(self.timePointList[0].runIdentifier.replicate)
        elif self.runIdentifier.strainID != '':
            return self.runIdentifier.strainID+\
                   self.runIdentifier.identifier1+\
                   self.runIdentifier.identifier2+\
                   str(self.runIdentifier.replicate)
        else:
            raise Exception("No unique ID or time points in titerObject()")

    def getReplicateID(self):
        #return self.runIdentifier
        return self.runIdentifier.strainID+self.runIdentifier.identifier1+self.runIdentifier.identifier2

class timeCourseObject(titerObject):
    #Object contains one time vector and one data vector
    def __init__(self):
        titerObject.__init__(self)
        self.timeVec = None
        self._dataVec = None
        self.rate = None

    # def returnCurveFitPoints(self, t):
    #    # print(self.rate)
    #    X0 = self.rate[0]
    #    K = self.rate[1]
    #    mu = self.rate[2]
    #    return np.divide(np.multiply(X0,K),(X0 + np.multiply((K-X0),np.exp(-mu*t))))
    #    # return self.rate[0]*self.rate[1]/(self.rate[0]+ (self.rate[1]-self.rate[0])*np.exp(-self.rate[2]*t))

    @property
    def dataVec(self):
        return self._dataVec

    @dataVec.setter
    def dataVec(self, dataVec):
        self._dataVec = dataVec
        if len(dataVec)>6:
            self.calcExponentialRate()

    def returnCurveFitPoints(self, t):
       # print(self.rate)
       A = self.rate[0]
       B = self.rate[1]
       C = self.rate[2]
       K = self.rate[3]
       Q = self.rate[4]
       nu = self.rate[5]
       return A + (    (K-A)      /     (     np.power((C+Q*np.exp(-B*t)),(1/nu))     )       )

    def addTimePoint(self, timePoint):
        self.timePointList.append(timePoint)
        if len(self.timePointList) == 1:
            self.runIdentifier = timePoint.runIdentifier
        else:
            for i in range(len(self.timePointList)-1):
                if self.timePointList[i].runIdentifier.returnUniqueID_singleExperiment() != self.timePointList[i+1].runIdentifier.returnUniqueID_singleExperiment():
                    raise Exception("runIdentifiers don't match within the timeCourse object")

        self.timePointList.sort(key=lambda timePoint: timePoint.t)
        self.timeVec = np.array([timePoint.t for timePoint in self.timePointList])
        self.dataVec = np.array([timePoint.titer for timePoint in self.timePointList])
        if len(self.timePointList)>6:
            self.calcExponentialRate()
        else:
            self.rate = [0,0,0,0,0,0]

    # def calcExponentialRate(self):
    #     #Define the growth equation to fit parameters
    #     def growthEquation(t, X0, K, mu):
    #         return np.divide(np.multiply(X0,K),(X0 + np.multiply((K-X0),np.exp(-mu*t))))
    #     #Fit and return the parameters
    #     flag = 0
    #     # try:
    #     gmod = Model(growthEquation)
    #     #Good params for OD data in seconds: X0 = 0.2, K = 0.2, mu = 0.0001
    #     params = gmod.make_params(X0 = 0.2, K = 0.02, mu = 0.1)
    #     gmod.set_param_hint('X0', value=0.2,min=0.13,max=0.25)
    #     #y = gmod.eval(t=self.timeVec,X0 = 0.1, K = 0.5, mu = 0.5)
    #     y=self.dataVec
    #     result = gmod.fit (y, t=self.timeVec,X0 = 0.2, K = 0.02, mu = 0.1, method = 'leastsq')
    #     # plt.plot(self.timeVec,y, 'bo')
    #     # plt.plot(self.timeVec,  result.init_fit,'k--')
    #     # plt.plot(self.timeVec, result.best_fit,'r-')
    #     # plt.show()
    #     self.rate = [0,0,0]
    #
    #     for key in result.best_values:
    #         if key == 'X0':
    #             self.rate[0] = result.best_values[key]
    #         if key == 'K':
    #             self.rate[1] = result.best_values[key]
    #         if key == 'mu':
    #             self.rate[2] = result.best_values[key]
        ################
        # if len(self.timeVec)>10:
        #     print(result.best_values)
        #     print(self.rate)
        #
        #     plt.plot(self.timeVec,y, 'bo')
        #     plt.plot(self.timeVec,  result.init_fit,'k--')
        #     plt.plot(self.timeVec, result.best_fit,'r-')
        #     plt.plot(self.timeVec,self.returnCurveFitPoints(self.timeVec),'g-')
        #     print(self.returnCurveFitPoints(self.timeVec))
        #     plt.show()

        # Test
        #     # popt=[0.01, 0.5, 0.5]
        #     # for i in range(5):
        #     #     popt, pcov = opt.curve_fit(growthEquation,self.timeVec,self.dataVec,popt)
        #     flag = 1

        # except:
        #     print("Optimal Parameters Not Found")
        #     self.rate =  [0,0,0]

        # if flag == 1:
        #     self.rate = popt
            #print("Growth rate ",self.rate)

    def calcExponentialRate(self):
        #Define the growth equation to fit parameters
        def growthEquation(t, A,B,C,K,Q,nu):
            return A + (    (K-A)      /     (     np.power((C+Q*np.exp(-B*t)),(1/nu))     )       )
            #return np.divide(np.multiply(X0,K),(X0 + np.multiply((K-X0),np.exp(-mu*t))))
        #Fit and return the parameters
        flag = 0
        # try:
        gmod = Model(growthEquation)
        #Good params for OD data in seconds: X0 = 0.2, K = 0.2, mu = 0.0001
        #params = gmod.make_params(A = 0.1, B=0.3, C=1, K = 0.5, Q = 0.1, nu = 0.5)#X0 = 0.2, K = 0.02, mu = 0.1)
        gmod.set_param_hint('A', value=np.mean(self.dataVec))#,min=0 ,max=min(self.dataVec)+0.05)
        gmod.set_param_hint('B',value=0.1)
        gmod.set_param_hint('C', value=1, vary=False)
        gmod.set_param_hint('Q', value=0.1)
        gmod.set_param_hint('K', value = max(self.dataVec))
        gmod.set_param_hint('nu', value=1, vary=False)
        params = gmod.make_params()
        #print(params)
        #y = gmod.eval(t=self.timeVec,X0 = 0.1, K = 0.5, mu = 0.5)
        result = gmod.fit (self.dataVec, params, t=self.timeVec, method = 'leastsq')
        #print(result.best_values)
        # plt.plot(self.timeVec,y, 'bo')
        # plt.plot(self.timeVec,  result.init_fit,'k--')
        # plt.plot(self.timeVec, result.best_fit,'r-')
        # plt.show()
        self.rate = [0,0,0,0,0,0]

        for key in result.best_values:
            if key == 'A':
                self.rate[0] = result.best_values[key]
            if key == 'B':
                self.rate[1] = result.best_values[key]
            if key == 'C':
                self.rate[2] = result.best_values[key]
            if key == 'K':
                self.rate[3] = result.best_values[key]
            if key == 'Q':
                self.rate[4] = result.best_values[key]
            if key == 'nu':
                self.rate[5] = result.best_values[key]
        # if len(self.dataVec)>10:
        #     print(result.best_values)
        #     print(self.rate)
        #
        #     plt.plot(self.timeVec,y, 'bo')
        #     #plt.plot(self.timeVec,  result.init_fit,'k--')
        #     #plt.plot(self.timeVec, result.best_fit,'r-')
        #     plt.plot(self.timeVec,self.returnCurveFitPoints(self.timeVec),'g-')
        #     print(self.returnCurveFitPoints(self.timeVec))
        #     plt.show()
class endPointObject(titerObject):
    def __init__(self, runID, t, data):
        titerObject.__init__(self, runID, t, data)

    def addTimePoint(self, timePoint):
        if len(self.timePointList) < 2:
            self.timePointList.append(timePoint)
        else:
            raise(Exception("Cannot have more than two timePoints for an endPoint Object"))

        if len(self.timePointList) == 2:
            self.timePointList.sort(key=lambda timePoint: timePoint.t)

# class productsObject(object):
#     def __init__(self, names, timeCourses):
#         self.names = names
#         self.timeCourses = timeCourses

class singleExperimentData(object):
    #Object contains a series of timeCourseObjects related to a single experiment
    def __init__(self):
        self._t = np.array([])
        self.titerObjectList = dict()
        self.ODKey = None
        self.productKeys = []
        self.substrateKey = None
        self.runIdentifier = runIdentifier()
        self._OD = None
        self._substrate = None
        self._products = dict()
        self.yields = dict()

    def addTiterObject(self, titerObject):
        if titerObject.runIdentifier.titerType == 'substrate':
            self.titerObjectList[titerObject.runIdentifier.titerName] = titerObject
            self._substrate = titerObject
            self.substrateKey = titerObject.runIdentifier.titerName
            self.calcSubstrateConsumed()

        if titerObject.runIdentifier.titerType == 'OD':
            self.titerObjectList[titerObject.runIdentifier.titerName] = titerObject
            self._OD = titerObject
            self.ODKey = titerObject.runIdentifier.titerName

        if titerObject.runIdentifier.titerType == 'product':
            self.titerObjectList[titerObject.runIdentifier.titerName] = titerObject
            self._products[titerObject.runIdentifier.titerName] = titerObject
            self.productKeys.append(titerObject.runIdentifier.titerName)

        if self.substrateKey != None and len(self.productKeys)>0:
            # print(self.substrateKey, self.productKeys)
            self.calcYield()

        self.checkTimeVectors()
        self.runIdentifier = titerObject.runIdentifier
        self.runIdentifier.time = None


    #Setters and Getters

    @property
    def OD(self):
        return self._OD

    @OD.setter
    def OD(self, OD):
        self._OD = OD
        self.checkTimeVectors()

    @property
    def substrate(self):
        return self._substrate

    @substrate.setter
    def substrate(self, substrate):
        self._substrate = substrate
        self.checkTimeVectors()
        self.calcSubstrateConsumed()
        if self._products:
            self.calcYield()

    @property
    def t(self):
        return self._t

    @t.setter
    def t(self, t):
        self._t = t

    @property
    def products(self):
        return self._products

    @products.setter
    def products(self, products):
        #print("setting products")
        self._products = products
        #print("substrate: ",self.__substrate)
        if self._substrate:
            self.calcYield()

    def setProduct(self, key, product):
        self.products[key] = product
        if self._substrate:
            self.calcYield()

    def checkTimeVectors(self):
        t = []
        flag = 0
        if self.OD:
            self._t = self.OD.timeVec
            t.append(self.OD.timeVec)

        if self.substrate != None:
            self._t = self.substrate.timeVec
            t.append(self.substrate.timeVec)

        if self.products:
            for key in self.products:
                self._t = self.products[key].timeVec
                t.append(self.products[key].timeVec)

        for i in range(len(t)-1):
            if (t[i] != t[i+1]).all():
                flag = 1

        if flag==1:
            raise(Exception("Time vectors within an experiment don't match, must implement new methods to deal with this type of data (if even possible)"))
        # else:
        #     self.__t = self.substrate.timeVec

    def getUniqueTimePointID(self):
        return self.substrate.runIdentifier.strainID+self.substrate.runIdentifier.identifier1+self.substrate.runIdentifier.identifier2+str(self.substrate.runIdentifier.replicate)

    def getUniqueReplicateID(self):
        #print(list(self.titerObjectList.keys()))
        return self.titerObjectList[list(self.titerObjectList.keys())[0]].getReplicateID()

    def calcSubstrateConsumed(self):
        self.substrateConsumed = np.empty([len(self.substrate.dataVec)])
        for timePointIndex in range(len(self.substrate.timeVec)):
            #print(timePointIndex)
            self.substrateConsumed[timePointIndex] = self.substrate.dataVec[0]-self.substrate.dataVec[timePointIndex]
        #return substrateConsumed

    def calcYield(self):
        self.yields = dict()
        for productKey in self.products:
            #print("product key: ",productKey)
            self.yields[productKey] = np.divide(self.products[productKey].dataVec,self.substrateConsumed)
            #print("yields: ",self.yields[productKey])

class singleExperimentDataShell(singleExperimentData):
    @singleExperimentData.substrate.setter
    def substrate(self, substrate):
        self._substrate = substrate

    @singleExperimentData.OD.setter
    def OD(self, OD):
        self._OD = OD

    @singleExperimentData.products.setter
    def products(self, products):
        self._products = products

class replicateExperimentObject(object):
    #Calculates statistics based on replicates
    def __init__(self):
        self.avg = singleExperimentDataShell()
        self.std = singleExperimentDataShell()
        self.t = None
        self.singleExperimentList = []
        self.runIdentifier = runIdentifier()
        #self.useReplicate = dict()
        #self.checkReplicateUniqueIDMatch()

    def checkReplicateUniqueIDMatch(self):
        #print('entered code')
        for i in range(len(self.singleExperimentList)-1):
            if self.singleExperimentList[i].getUniqueReplicateID() != self.singleExperimentList[i+1].getUniqueReplicateID():
                raise Exception("the replicates do not have the same uniqueID, either the uniqueID includes too much information or the strains don't match")

            if (self.singleExperimentList[i].t != self.singleExperimentList[i+1].t).all():
                raise Exception("time vectors don't match within replicates")
            else:
                self.t = self.singleExperimentList[i].t

            if False and len(self.singleExperimentList[i].substrate.dataVec) != len(self.singleExperimentList[i+1].substrate.dataVec): #TODO
                print("Time Vector 1: ",self.singleExperimentList[i].t,"\nTime Vector 2: ",self.singleExperimentList[i+1].t)
                print("Vector 1: ",self.singleExperimentList[i].substrate.dataVec,"\nVector 2: ",self.singleExperimentList[i+1].substrate.dataVec)
                raise(Exception("length of substrate vectors do not match"))

            for key in self.singleExperimentList[i].products:
                if len(self.singleExperimentList[i].products[key].dataVec) != len(self.singleExperimentList[i+1].products[key].dataVec):
                    raise(Exception("length of product vector "+str(key)+" do not match"))

    def addReplicateExperiment(self, newReplicateExperiment):
        self.singleExperimentList.append(newReplicateExperiment)
        if len(self.singleExperimentList)==1:
            self.t = self.singleExperimentList[0].t
        self.checkReplicateUniqueIDMatch()
        self.calcAverageAndDev()
        self.runIdentifier = newReplicateExperiment.runIdentifier
        self.runIdentifier.replicate = None
        self.runIdentifier.time = None

    def calcAverageAndDev(self):    #Calculate averages
        #First check what data exists

        ODflag = 0
        productFlag = 0
        substrateFlag = 0
        yieldFlag = 0
        for singleExperiment in self.singleExperimentList:
            if singleExperiment.OD:
                ODflag = 1
            if singleExperiment.products:
                productFlag = 1 #TODO need to make generic for different products in different expts
            if singleExperiment.substrate:
                substrateFlag=1
            if singleExperiment.yields:
                yieldFlag = 1

        if ODflag == 1:
            self.avg.OD = timeCourseObject()
            self.std.OD = timeCourseObject()
            #print([singleExperimentObject.OD.dataVec for singleExperimentObject in self.singleExperimentList])
            self.avg.OD.timeVec = self.t
            self.avg.OD.dataVec = np.mean([singleExperimentObject.OD.dataVec for singleExperimentObject in self.singleExperimentList], axis=0)
            self.std.OD.dataVec = np.std([singleExperimentObject.OD.dataVec for singleExperimentObject in self.singleExperimentList], axis=0)
            self.std.OD.dataVec = np.std([singleExperimentObject.OD.dataVec for singleExperimentObject in self.singleExperimentList], axis=0)
            self.avg.OD.rate = np.mean([singleExperimentObject.OD.rate for singleExperimentObject in self.singleExperimentList], axis=0)#calcExponentialRate()
            self.std.OD.rate = np.std([singleExperimentObject.OD.rate for singleExperimentObject in self.singleExperimentList], axis=0)
            #print([singleExperimentObject.OD.rate for singleExperimentObject in self.singleExperimentList])

        if productFlag == 1:
            for key in self.singleExperimentList[0].products:
                self.avg.products[key] = timeCourseObject()
                self.std.products[key] = timeCourseObject()
                self.avg.products[key].dataVec = np.mean([singleExperimentObject.products[key].dataVec for singleExperimentObject in self.singleExperimentList],axis=0)
                self.std.products[key].dataVec = np.std([singleExperimentObject.products[key].dataVec for singleExperimentObject in self.singleExperimentList],axis=0)
                #print([singleExperimentObject.products[key].rate for singleExperimentObject in self.singleExperimentList])
                self.avg.products[key].rate = np.mean([singleExperimentObject.products[key].rate for singleExperimentObject in self.singleExperimentList],axis=0)

                # for singleExperimentObject in self.singleExperimentList:
                #     singleExperimentObject.products[key].calcExponentialRate()
                #     # print(singleExperimentObject.products[key].rate)

        if substrateFlag == 1:
            self.avg.substrate = np.mean([singleExperimentObject.substrate.dataVec for singleExperimentObject in self.singleExperimentList], axis=0)
            self.std.substrate = np.std([singleExperimentObject.substrate.dataVec for singleExperimentObject in self.singleExperimentList], axis=0)

        if yieldFlag == 1:
            for key in self.singleExperimentList[0].yields:
                self.avg.yields[key] = np.mean([singleExperimentObject.yields[key] for singleExperimentObject in self.singleExperimentList],axis=0)
                self.std.yields[key] = np.std([singleExperimentObject.yields[key] for singleExperimentObject in self.singleExperimentList],axis=0)


