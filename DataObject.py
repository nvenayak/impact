__author__ = 'Naveen Venayak'

import numpy as np
import scipy.optimize as opt
from lmfit import Model
import matplotlib.pyplot as plt
import time
######################################################################################################################
#####    This is the project container. This is the ultimate wrapper for all data and plotting functions           ###
######################################################################################################################
class projectContainer(object):

    def __init__(self):
        self.timePointDict = dict()
        self.titerObjectDict = dict()
        self.singleExperimentObjectDict = dict()
        self.replicateExperimentObjectDict = dict()

    def parseTimePointCollection(self, timePointCollection):
        for timePoint in timePointCollection:
            flag = 0
            for titerObjectKey in self.titerObjectDict:
                if timePoint[list(timePoint.keys())[0]].getUniqueTimePointID() == self.titerObjectDict[titerObjectKey][list(timePoint.keys())[0]].getTimeCourseID(): ##TODO We can check only one key since they should all be the same, this will be checked later
                    for key in self.titerObjectDict[titerObjectKey]:
                        self.titerObjectDict[titerObjectKey][key].addTimePoint(timePoint[key])
                    flag = 1
                    break
            if flag == 0:
                self.titerObjectDict[timePoint[list(timePoint.keys())[0]].getUniqueTimePointID()] = dict()
                for key in timePoint:
                    self.titerObjectDict[timePoint[key].getUniqueTimePointID()][key] = timeCourseObject()
                    self.titerObjectDict[timePoint[key].getUniqueTimePointID()][key].addTimePoint(timePoint[key])

    def parseTiterObjectCollection(self, titerObjectList, titerODFlag):
        if titerODFlag=='titer':
            print('entered here')
            for key in titerObjectList: #Go through each titerObjectList
                self.singleExperimentObjectDict[key] = singleExperimentData()
                for key2 in titerObjectList[key]:
                    self.singleExperimentObjectDict[key].addTiterObject(titerObjectList[key][key2])
        elif titerODFlag == 'OD':
            for key in titerObjectList:
                self.singleExperimentObjectDict[key] = singleExperimentData()
                self.singleExperimentObjectDict[key].addTiterObject(titerObjectList[key])
        else:
            raise Exception("No titer/OD flag set")

        self.parseSingleExperimentObjectList(self.singleExperimentObjectDict)

    def parseSingleExperimentObjectList(self, singleExperimentObjectList):
        for key in singleExperimentObjectList:
            flag = 0
            for key2 in self.replicateExperimentObjectDict:
                #print(key2, singleExperimentObjectList[key].getUniqueReplicateID())
                if key2 == singleExperimentObjectList[key].getUniqueReplicateID():
                    #print("Replicate found")
                    self.replicateExperimentObjectDict[key2].addReplicateExperiment(singleExperimentObjectList[key])
                    flag = 1
                    break
            if flag == 0:
                self.replicateExperimentObjectDict[singleExperimentObjectList[key].getUniqueReplicateID()] = replicateExperimentObject()
                self.replicateExperimentObjectDict[singleExperimentObjectList[key].getUniqueReplicateID()].addReplicateExperiment(singleExperimentObjectList[key])

    def printGenericTimeCourse(self, strainsToPlot, titersToPlot):
        colorMap = 'Set3'

        # Determine optimal figure size
        if len(titersToPlot) == 1:
            figureSize = (12,6)
        if len(titersToPlot) > 1:
            figureSize = (12,3.5)
        if len(titersToPlot) > 4:
            figureSize = (12,7)

        plt.figure(figsize=figureSize)

        colors = plt.get_cmap(colorMap)(np.linspace(0,1,len(strainsToPlot)))

        pltNum = 0
        for product in titersToPlot:
            pltNum += 1

            # Choose the subplot layout
            if len(titersToPlot) == 1:
                ax = plt.subplot(111)
            if len(titersToPlot) > 1:
                ax = plt.subplot(1,len(titersToPlot),pltNum)
            if len(titersToPlot) > 4:
                ax = plt.subplot(2,len(titersToPlot),pltNum)

            # Set some axis aesthetics
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            colorIndex = 0
            handle = dict()
            xlabel = 'Time (hours)'
            for key in strainsToPlot:
                xData = self.replicateExperimentObjectDict[key].t
                if product == 'OD':
                    removePointFraction = 6 #

                    scaledTime = self.replicateExperimentObjectDict[key].t
                    # Plot the data
                    handle[key] = plt.plot(np.linspace(min(scaledTime),max(scaledTime),50),
                                            self.replicateExperimentObjectDict[key].avg.OD.returnCurveFitPoints(np.linspace(min(self.replicateExperimentObjectDict[key].t),max(self.replicateExperimentObjectDict[key].t),50)),
                                           '-',lw=1.5,color=colors[colorIndex])
                    # Plot the fit curve
                    handle[key] = plt.errorbar(scaledTime[::removePointFraction],
                                               self.replicateExperimentObjectDict[key].avg.OD.dataVec[::removePointFraction],
                                               self.replicateExperimentObjectDict[key].std.OD.dataVec[::removePointFraction],
                                               lw=2.5,elinewidth=1,capsize=2,fmt='o',markersize=5,color=colors[colorIndex])
                    # Fill in the error bar range
                    plt.fill_between(scaledTime,self.replicateExperimentObjectDict[key].avg.OD.dataVec+self.replicateExperimentObjectDict[key].std.OD.dataVec,
                                     self.replicateExperimentObjectDict[key].avg.OD.dataVec-self.replicateExperimentObjectDict[key].std.OD.dataVec,
                                     facecolor=colors[colorIndex],alpha=0.1)
                    # Add growth rates at end of curve
                    plt.text(scaledTime[-1]+0.5,
                             self.replicateExperimentObjectDict[key].avg.OD.returnCurveFitPoints(np.linspace(min(self.replicateExperimentObjectDict[key].t),max(self.replicateExperimentObjectDict[key].t),50))[-1],
                             '$\mu$ = '+'{:.2f}'.format(self.replicateExperimentObjectDict[key].avg.OD.rate[1]) + ' $\pm$ ' + '{:.2f}'.format(self.replicateExperimentObjectDict[key].std.OD.rate[1]),
                             verticalalignment='center')
                    ylabel = 'OD600'
                else:
                    yData = self.replicateExperimentObjectDict[key].avg.products[product].dataVec
                    handle[key] = plt.errorbar(self.replicateExperimentObjectDict[key].t,self.replicateExperimentObjectDict[key].avg.products[product].dataVec,self.replicateExperimentObjectDict[key].std.products[product].dataVec,lw=2.5,elinewidth=1,capsize=2,fmt='o-',color=colors[colorIndex])
                    ylabel = product+" Titer (g/L)"

                colorIndex += 1

        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        ymin, ymax = plt.ylim()
        xmin, xmax = plt.xlim()
        plt.xlim([0,xmax*1.2])
        plt.ylim([0,ymax])
        plt.tight_layout()
        plt.tick_params(right="off",top="off")
        plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0, frameon=False)
        plt.subplots_adjust(right=0.7)

        if len(titersToPlot) == 1:
            plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0)
            plt.subplots_adjust(right=0.7)
        if len(titersToPlot) > 1:
            plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.15, 0.5), loc=6, borderaxespad=0)
            plt.subplots_adjust(right=0.75)
        if len(titersToPlot) > 4:
            raise Exception("Plotting >4 plots is unimplemented functionality")

        # Save the figure
        plt.savefig('Figures/'+time.strftime('%y')+'.'+time.strftime('%m')+'.'+time.strftime('%d')+" H"+time.strftime('%H')+'-M'+time.strftime('%M')+'-S'+time.strftime('%S')+'.png')

    def printGrowthRateBarChart(replicateExperimentObjectList, strainsToPlot, sortBy):
        handle = dict()

        plt.figure(figsize=(9, 5))

        ax = plt.subplot(111)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)


        uniques = list(set([getattr(replicateExperimentObjectList[key].runIdentifier,sortBy) for key in strainsToPlot]))
        uniques.sort()
        #Find max number of samples
        maxSamples = 0
        for unique in uniques:
            if len([replicateExperimentObjectList[key].avg.OD.rate[1] for key in strainsToPlot if getattr(replicateExperimentObjectList[key].runIdentifier,sortBy) == unique]) > maxSamples:
                maxSamples = len([replicateExperimentObjectList[key].avg.OD.rate[1] for key in strainsToPlot if getattr(replicateExperimentObjectList[key].runIdentifier,sortBy) == unique])
                maxIndex = unique

        barWidth = 0.9/len(uniques)
        index = np.arange(maxSamples)
        colors = plt.get_cmap('Set2')(np.linspace(0,1.0,len(uniques)))

        i = 0
        for unique in uniques:
            print(unique)
            handle[unique] = plt.bar(index[0:len([replicateExperimentObjectList[key].avg.OD.rate[1] for key in strainsToPlot if getattr(replicateExperimentObjectList[key].runIdentifier,sortBy) == unique])],
                    [replicateExperimentObjectList[key].avg.OD.rate[1] for key in strainsToPlot if getattr(replicateExperimentObjectList[key].runIdentifier,sortBy) == unique],
                    barWidth, yerr=[replicateExperimentObjectList[key].std.OD.rate[1] for key in strainsToPlot if getattr(replicateExperimentObjectList[key].runIdentifier,sortBy) == unique],
                    color = colors[i],ecolor='k',capsize=5,error_kw=dict(elinewidth=1, capthick=1))
            #xaxislabels.append
            i += 1
            index = index+barWidth

        ax.yaxis.set_ticks_position('left')
        ax.xaxis.set_ticks_position('bottom')
        plt.ylabel('Growth Rate ($\mu$, h$^{-1}$)')
        xticklabel = ''
        for attribute in ['strainID','identifier1','identifier2']:
            if attribute != sortBy:
                xticklabel = xticklabel+attribute

        if 'strainID' == sortBy:
            tempticks =[replicateExperimentObjectList[key].runIdentifier.identifier1+'+'+replicateExperimentObjectList[key].runIdentifier.identifier2 for key in strainsToPlot if getattr(replicateExperimentObjectList[key].runIdentifier,sortBy) == maxIndex]
        if 'identifier1' == sortBy:
            tempticks = [replicateExperimentObjectList[key].runIdentifier.strainID +'+'+replicateExperimentObjectList[key].runIdentifier.identifier2 for key in strainsToPlot if getattr(replicateExperimentObjectList[key].runIdentifier,sortBy) == maxIndex]
        if 'identifier2' == sortBy:
            tempticks = [replicateExperimentObjectList[key].runIdentifier.strainID +'+'+replicateExperimentObjectList[key].runIdentifier.identifier1 for key in strainsToPlot if getattr(replicateExperimentObjectList[key].runIdentifier,sortBy) == maxIndex]

        plt.xticks(index-barWidth,
                   tempticks,
                    #if getattr(replicateExperimentObjectList[key].runIdentifier,sortBy) == maxIndex],
                   rotation='45', ha='right', va='top')
        plt.tight_layout()
        plt.subplots_adjust(right=0.75)
        #print([handle[key][0][0] for key in handle])
        plt.legend([handle[key][0] for key in uniques],uniques,bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0)

    def printEndPointYield(self, strainsToPlot, withLegend):
        replicateExperimentObjectList = self.replicateExperimentObjectList
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

    def printYieldTimeCourse(self, strainsToPlot):
        replicateExperimentObjectList = self.replicateExperimentObjectList
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
            #print(tempParsedIdentifier)
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
    #-----------------------------------Object contains one time vector and one data vector-----------------------------
    def __init__(self):
        titerObject.__init__(self)
        self.timeVec = None
        self._dataVec = None
        self.rate = None

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
        gmod.set_param_hint('A', value=np.mean(self.dataVec), min=0)#,min=0 ,max=min(self.dataVec)+0.05)
        gmod.set_param_hint('B',value=0.1)
        gmod.set_param_hint('C', value=1, vary=False)
        gmod.set_param_hint('Q', value=0.1, max = 10)
        gmod.set_param_hint('K', value = max(self.dataVec), max=5)
        gmod.set_param_hint('nu', value=1, vary=False)
        params = gmod.make_params()
        #print(params)
        #y = gmod.eval(t=self.timeVec,X0 = 0.1, K = 0.5, mu = 0.5)
        result = gmod.fit (self.dataVec, params, t=self.timeVec, method = 'nelder')
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

    # def returnCurveFitPoints(self, t):
    #    # print(self.rate)
    #    X0 = self.rate[0]
    #    K = self.rate[1]
    #    mu = self.rate[2]
    #    return np.divide(np.multiply(X0,K),(X0 + np.multiply((K-X0),np.exp(-mu*t))))
    #    # return self.rate[0]*self.rate[1]/(self.rate[0]+ (self.rate[1]-self.rate[0])*np.exp(-self.rate[2]*t))

class endPointObject(titerObject):
    def __init__(self, runID, t, data):
        titerObject.__init__(self, runID, t, data)

    def addTimePoint(self, timePoint):
        if len(self.timePointList) < 2:
            self.timePointList.append(timePoint)
        else:
            raise Exception("Cannot have more than two timePoints for an endPoint Object")

        if len(self.timePointList) == 2:
            self.timePointList.sort(key=lambda timePoint: timePoint.t)

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

    # --------------------------- Setters and Getters
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
        self._products = products
        if self._substrate:
            self.calcYield()

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

    def checkTimeVectors(self):
        t = []
        flag = 0
        if self.OD:
            self._t = self.OD.timeVec
            t.append(self.OD.timeVec)

        if self.substrate:
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

    def getUniqueTimePointID(self):
        return self.substrate.runIdentifier.strainID+self.substrate.runIdentifier.identifier1+self.substrate.runIdentifier.identifier2+str(self.substrate.runIdentifier.replicate)

    def getUniqueReplicateID(self):
        return self.titerObjectList[list(self.titerObjectList.keys())[0]].getReplicateID()

    def calcSubstrateConsumed(self):
        self.substrateConsumed = np.empty([len(self.substrate.dataVec)])
        for timePointIndex in range(len(self.substrate.timeVec)):
            self.substrateConsumed[timePointIndex] = self.substrate.dataVec[0]-self.substrate.dataVec[timePointIndex]

    def calcYield(self):
        self.yields = dict()
        for productKey in self.products:
            self.yields[productKey] = np.divide(self.products[productKey].dataVec,self.substrateConsumed)

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
        self.useReplicate = dict()
        #self.checkReplicateUniqueIDMatch()

    def checkReplicateUniqueIDMatch(self):
        for i in range(len(self.singleExperimentList)-1):
            if self.singleExperimentList[i].getUniqueReplicateID() != self.singleExperimentList[i+1].getUniqueReplicateID():
                raise Exception("the replicates do not have the same uniqueID, either the uniqueID includes too much information or the strains don't match")

            if (self.singleExperimentList[i].t != self.singleExperimentList[i+1].t).all():
                raise Exception("time vectors don't match within replicates")
            else:
                self.t = self.singleExperimentList[i].t

            if len(self.singleExperimentList[i].t) != len(self.singleExperimentList[i+1].t): #TODO
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
            self.avg.OD.timeVec = self.t
            self.avg.OD.dataVec = np.mean([singleExperimentObject.OD.dataVec for singleExperimentObject in self.singleExperimentList], axis=0)
            self.std.OD.dataVec = np.std([singleExperimentObject.OD.dataVec for singleExperimentObject in self.singleExperimentList], axis=0)
            self.std.OD.dataVec = np.std([singleExperimentObject.OD.dataVec for singleExperimentObject in self.singleExperimentList], axis=0)
            self.avg.OD.rate = np.mean([singleExperimentObject.OD.rate for singleExperimentObject in self.singleExperimentList], axis=0)#calcExponentialRate()
            self.std.OD.rate = np.std([singleExperimentObject.OD.rate for singleExperimentObject in self.singleExperimentList], axis=0)

        if productFlag == 1:
            for key in self.singleExperimentList[0].products:
                self.avg.products[key] = timeCourseObject()
                self.std.products[key] = timeCourseObject()
                self.avg.products[key].dataVec = np.mean([singleExperimentObject.products[key].dataVec for singleExperimentObject in self.singleExperimentList],axis=0)
                self.std.products[key].dataVec = np.std([singleExperimentObject.products[key].dataVec for singleExperimentObject in self.singleExperimentList],axis=0)
                self.avg.products[key].rate = np.mean([singleExperimentObject.products[key].rate for singleExperimentObject in self.singleExperimentList],axis=0)

        if substrateFlag == 1:
            self.avg.substrate = np.mean([singleExperimentObject.substrate.dataVec for singleExperimentObject in self.singleExperimentList], axis=0)
            self.std.substrate = np.std([singleExperimentObject.substrate.dataVec for singleExperimentObject in self.singleExperimentList], axis=0)

        if yieldFlag == 1:
            for key in self.singleExperimentList[0].yields:
                self.avg.yields[key] = np.mean([singleExperimentObject.yields[key] for singleExperimentObject in self.singleExperimentList],axis=0)
                self.std.yields[key] = np.std([singleExperimentObject.yields[key] for singleExperimentObject in self.singleExperimentList],axis=0)