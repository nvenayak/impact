__author__ = 'Naveen Venayak'

import numpy as np
import scipy.optimize as opt
import matplotlib.pyplot as plt

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
        self.uniqueID = runIdentifier()

    def addTimePoint(self, timePoint):
        raise(Exception("No addTimePoint method defiend in the child"))

    def getTimeCourseID(self):
        if len(self.timePointList)>0:
            return self.timePointList[0].runIdentifier.strainID+\
                   self.timePointList[0].runIdentifier.identifier1+\
                   self.timePointList[0].runIdentifier.identifier2+\
                   str(self.timePointList[0].runIdentifier.replicate)
        elif self.uniqueID.strainID != '':
            return self.uniqueID.strainID+\
                   self.uniqueID.identifier1+\
                   self.uniqueID.identifier2+\
                   str(self.uniqueID.replicate)
        else:
            raise Exception("No unique ID or time points in titerObjet()")


    def getReplicateID(self):
        return self.timePointList[0].runIdentifier.strainID+self.timePointList[0].runIdentifier.identifier1+self.timePointList[0].runIdentifier.identifier2

class timeCourseObject(titerObject):
    #Object contains one time vector and one data vector
    def __init__(self):
        titerObject.__init__(self)
        self.timeVec = None
        self.dataVec = None
        self.rate = None

    def returnCurveFitPoints(self, t):
       # print(self.rate)
        return self.rate[0]*self.rate[1]/(self.rate[0]+ (self.rate[1]-self.rate[0])*np.exp(-self.rate[2]*t))

    def addTimePoint(self, timePoint):
        self.timePointList.append(timePoint)
        self.timePointList.sort(key=lambda timePoint: timePoint.t)
        self.timeVec = np.array([timePoint.t for timePoint in self.timePointList])
        self.dataVec = np.array([timePoint.titer for timePoint in self.timePointList])
        if len(self.timePointList)>6:
            self.calcExponentialRate()
        else:
            self.rate = [0,0,0]

    def calcExponentialRate(self):
        #Define the growth equation to fit parameters
        def growthEquation(t, X0, K, mu):
            return X0*K/(X0+ (K-X0)*np.exp(-mu*t))
        #Fit and return the parameters
        flag = 0
        try:
            popt=[0.01, 0.1, 1]
            for i in range(1):
                popt, pcov = opt.curve_fit(growthEquation,self.timeVec,self.dataVec,popt)
            flag = 1
        except:
            print("Optimal Parameters Not Found")
            self.rate =  [0,0,0]

        if flag == 1:
            self.rate = popt
            #print("Growth rate ",self.rate)

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
        self.__products = dict()
        self.yields = dict()

    #Setters and Getters
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
        self.calcSubstrateConsumed()
        if self.__products:
            self.calcYield()

    @property
    def t(self):
        return self.__t

    @t.setter
    def t(self, t):
        self.__t = t

    @property
    def products(self):
        return self.__products

    @products.setter

    def products(self, products):
        #print("setting products")
        self.__products = products
        #print("substrate: ",self.__substrate)
        if self.__substrate:
            self.calcYield()

    def setProduct(self, key, product):
        self.products[key] = product
        if self.__substrate:
            self.calcYield()

    def checkTimeVectors(self):
        t = []
        flag = 0
        if self.OD:
            t.append(self.OD.timeVec)
        if self.substrate != None:
            t.append(self.substrate.timeVec)

        if self.products:
            for key in self.products:
                t.append(self.products[key].timeVec)

        for i in range(len(t)-1):
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

    def calcSubstrateConsumed(self): #TODO implement function
        self.substrateConsumed = np.empty([len(self.substrate.dataVec)])
        for timePointIndex in range(len(self.substrate.timeVec)):
            #print(timePointIndex)
            self.substrateConsumed[timePointIndex] = self.substrate.dataVec[0]-self.substrate.dataVec[timePointIndex]
        #return substrateConsumed

    def calcYield(self): #TODO implement function
        self.yields = dict()
        for productKey in self.products:
            #print("product key: ",productKey)
            self.yields[productKey] = np.divide(self.products[productKey].dataVec,self.substrateConsumed)
            #print("yields: ",self.yields[productKey])

class singleExperimentDataShell(singleExperimentData):
    @singleExperimentData.substrate.setter
    def substrate(self, substrate):
        self.__substrate = substrate

    @singleExperimentData.OD.setter
    def OD(self, OD):
        self.__OD = OD

    @singleExperimentData.products.setter
    def products(self, products):
        self.__products = products

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

    def calcAverageAndDev(self):    #Calculate averages
        #First check what data exists

        ODflag = 0
        productFlag = 0
        substrateFlag = 0
        yieldFlag = 0
        for singleExperiment in self.singleExperimentList:
            # TODO timePoint,
            if singleExperiment.OD:
                ODflag = 1
            if singleExperiment.products:
                productFlag = 1 #TODO need to make generic for different products in different expts
            if singleExperiment.substrate:
                substrateFlag=1
            if singleExperiment.yields:
                yieldFlag = 1

        if ODflag == 1:
            self.avg.OD = np.mean([singleExperimentObject.OD.dataVec for singleExperimentObject in self.singleExperimentList], axis=0)
            self.std.OD = np.std([singleExperimentObject.OD.dataVec for singleExperimentObject in self.singleExperimentList], axis=0)

        if productFlag == 1:
            for key in self.singleExperimentList[0].products:
                self.avg.products[key] = timeCourseObject()
                self.std.products[key] = timeCourseObject()
                self.avg.products[key].dataVec = np.mean([singleExperimentObject.products[key].dataVec for singleExperimentObject in self.singleExperimentList],axis=0)
                self.std.products[key].dataVec = np.std([singleExperimentObject.products[key].dataVec for singleExperimentObject in self.singleExperimentList],axis=0)
                #print([singleExperimentObject.products[key].rate for singleExperimentObject in self.singleExperimentList])
                self.avg.products[key].rate = np.mean([singleExperimentObject.products[key].rate for singleExperimentObject in self.singleExperimentList],axis=0)
                for singleExperimentObject in self.singleExperimentList:
                    singleExperimentObject.products[key].calcExponentialRate()
                    print(singleExperimentObject.products[key].rate)

        if substrateFlag == 1:
            self.avg.substrate = np.mean([singleExperimentObject.substrate.dataVec for singleExperimentObject in self.singleExperimentList], axis=0)
            self.std.substrate = np.std([singleExperimentObject.substrate.dataVec for singleExperimentObject in self.singleExperimentList], axis=0)

        if yieldFlag == 1:
            for key in self.singleExperimentList[0].yields:
                self.avg.yields[key] = np.mean([singleExperimentObject.yields[key] for singleExperimentObject in self.singleExperimentList],axis=0)
                self.std.yields[key] = np.std([singleExperimentObject.yields[key] for singleExperimentObject in self.singleExperimentList],axis=0)
                #print(self.avg.yields[key])

def printTimeCourse(replicateExperimentObjectList, strainsToPlot):
    # You typically want your plot to be ~1.33x wider than tall. This plot is a rare
    # exception because of the number of lines being plotted on it.
    # Common sizes: (10, 7.5) and (12, 9)
    plt.figure(figsize=(12, 3.5))

    handle = dict()
    colors = plt.get_cmap('Set3')(np.linspace(0,1,len(strainsToPlot)))

    #plt.hold(False)
    product = "Ethanol"
    pltNum = 0
    plt.subplot(141)
    for product in replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products:
        pltNum += 1
        ax = plt.subplot(1,len(replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products),pltNum)
        ax.spines["top"].set_visible(False)
        #ax.spines["bottom"].set_visible(False)
        ax.spines["right"].set_visible(False)
        #ax.spines["left"].set_visible(False)
        colorIndex = 0
        for key in strainsToPlot:
            handle[key] = plt.errorbar(replicateExperimentObjectList[key].t,replicateExperimentObjectList[key].avg.products[product].dataVec,replicateExperimentObjectList[key].std.products[product].dataVec,lw=2.5,elinewidth=1,capsize=2,fmt='o-',color=colors[colorIndex])
            print(replicateExperimentObjectList[key].avg.products[product].rate)
            # handle[key] = plt.plot(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50),
            #                                    replicateExperimentObjectList[key].avg.products[product].returnCurveFitPoints(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50)),'-',lw=2.5,color=colors[colorIndex])
            colorIndex += 1
        plt.xlabel("Time (hours)")
        plt.ylabel(product+" Titer (g/L)")
        ymin, ymax = plt.ylim()
        plt.ylim([0,ymax])
        plt.tight_layout()
        plt.tick_params(right="off",top="off")
    #plt.subplot(1,4,4)
    plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.15, 0.5), loc=6, borderaxespad=0)
    plt.subplots_adjust(right=0.75)

    #plt.show()

def printYieldTimeCourse(replicateExperimentObjectList, strainsToPlot):
    # You typically want your plot to be ~1.33x wider than tall. This plot is a rare
    # exception because of the number of lines being plotted on it.
    # Common sizes: (10, 7.5) and (12, 9)
    plt.figure(figsize=(12, 3))

    handle = dict()
    barWidth = 0.9/len(strainsToPlot)
    #plt.hold(False)
    pltNum = 0
    colors = plt.get_cmap('Paired')(np.linspace(0,1.0,len(strainsToPlot)))
    for product in replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products:
        pltNum += 1
        ax = plt.subplot(1,len(replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products)+1,pltNum)
        ax.spines["top"].set_visible(False)
        #ax.spines["bottom"].set_visible(False)
        ax.spines["right"].set_visible(False)
        #ax.spines["left"].set_visible(False)
        location = 0
        colorIndex = 0
        for key in strainsToPlot:
            index = np.arange(len(replicateExperimentObjectList[key].t))
            handle[key] = plt.bar(index+location,replicateExperimentObjectList[key].avg.yields[product],barWidth,yerr=replicateExperimentObjectList[key].std.yields[product],color=colors[colorIndex],ecolor='k')
            plt.xticks(index + barWidth, replicateExperimentObjectList[key].t)
            location += barWidth
            colorIndex += 1
            # print(replicateExperimentObjectList[key].avg.products[product].rate)
            # handle[key] = plt.plot(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50),
            #                                    replicateExperimentObjectList[key].avg.products[product].returnCurveFitPoints(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50)),'-',lw=2.5)
        plt.xlabel("Time (hours)")
        plt.ylabel(product+" Yield (g/g)")
        ymin, ymax = plt.ylim()
        plt.ylim([0,1])
        plt.tight_layout()
    #plt.subplot(1,4,4)
    plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.15, 0.5), loc=6, borderaxespad=0)
    plt.subplots_adjust(right=1.05)

def printEndPointYield(replicateExperimentObjectList, strainsToPlot, withLegend):


    handle = dict()
    colors = plt.get_cmap('Set2')(np.linspace(0,1.0,len(strainsToPlot)))

    barWidth = 0.6
    pltNum = 0



    if withLegend == 0:
        plt.figure(figsize=(6, 3))
        for product in replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products:
            endPointTiterAvg = []
            endPointTiterStd = []
            endPointTiterLabel = []
            pltNum += 1
            #ax = plt.subplot(0.8)
            ax = plt.subplot(1,len(replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products),pltNum)
            ax.spines["top"].set_visible(False)
            #ax.spines["bottom"].set_visible(False)
            ax.spines["right"].set_visible(False)
            #ax.spines["left"].set_visible(False)
            location = 0
            index = np.arange(len(strainsToPlot))

            for key in strainsToPlot:
                endPointTiterLabel.append(key)
                endPointTiterAvg.append(replicateExperimentObjectList[key].avg.yields[product][-1])
                endPointTiterStd.append(replicateExperimentObjectList[key].std.yields[product][-1])
            handle[key] = plt.bar(index,endPointTiterAvg,barWidth,yerr=endPointTiterStd,color=plt.get_cmap('Pastel1')(0.25),ecolor='black',capsize=5,error_kw=dict(elinewidth=1, capthick=1) )
            location += barWidth
            plt.xlabel("Time (hours)")
            plt.ylabel(product+" Yield (g/g)")
            ymin, ymax = plt.ylim()
            plt.ylim([0,ymax])
            plt.tight_layout()
            plt.xticks(index + barWidth/2, endPointTiterLabel,rotation='45', ha='right', va='top')
            ax.yaxis.set_ticks_position('left')
            ax.xaxis.set_ticks_position('bottom')
    if withLegend == 1:
        plt.figure(figsize=(6, 2))

        for product in replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products:
            endPointTiterAvg = []
            endPointTiterStd = []
            endPointTiterLabel = []
            pltNum += 1
            ax = plt.subplot(1,len(replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products),pltNum)
            ax.spines["top"].set_visible(False)
            #ax.spines["bottom"].set_visible(False)
            ax.spines["right"].set_visible(False)
            #ax.spines["left"].set_visible(False)
            location = 0
            index = np.arange(len(strainsToPlot))

            for key in strainsToPlot:
                endPointTiterLabel.append(key)
                endPointTiterAvg.append(replicateExperimentObjectList[key].avg.yields[product][-1])
                endPointTiterStd.append(replicateExperimentObjectList[key].std.yields[product][-1])

            barList = plt.bar(index,endPointTiterAvg,barWidth,yerr=endPointTiterStd,ecolor='k')
            count = 0
            for bar, count in zip(barList, range(len(strainsToPlot))):
                bar.set_color(colors[count])
            location += barWidth
            plt.ylabel(product+" Titer (g/L)")
            ymin, ymax = plt.ylim()
            plt.ylim([0,ymax])
            plt.tight_layout()
            plt.xticks([])
            ax.yaxis.set_ticks_position('left')
            ax.xaxis.set_ticks_position('bottom')
        plt.subplots_adjust(right=0.7)
        plt.legend(barList,strainsToPlot,bbox_to_anchor=(1.15, 0.5), loc=6, borderaxespad=0)

