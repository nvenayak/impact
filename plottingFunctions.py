__author__ = 'Naveen'

import numpy as np
import matplotlib.pyplot as plt

def printGenericTimeCourse(replicateExperimentObjectList, strainsToPlot, titersToPlot):
    colorMap = 'Set3'

    ## Determine optimal figure size
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

        #Choose the subplot layout
        if len(titersToPlot) == 1:
            ax = plt.subplot(111)
        if len(titersToPlot) > 1:
            ax = plt.subplot(1,len(titersToPlot),pltNum)
        if len(titersToPlot) > 4:
            ax = plt.subplot(2,len(titersToPlot),pltNum)

        #Set some axis aesthetics
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        colorIndex = 0
        handle = dict()
        xlabel = 'Time (hours)'
        for key in strainsToPlot:
            xData = replicateExperimentObjectList[key].t
            if product == 'OD':
                scaledTime = np.divide(replicateExperimentObjectList[key].t,3600)
                handle[key] = plt.errorbar(scaledTime,replicateExperimentObjectList[key].avg.OD.dataVec,replicateExperimentObjectList[key].std.OD.dataVec,lw=2.5,elinewidth=1,capsize=2,fmt='o-',color=colors[colorIndex])
                plt.fill_between(scaledTime,replicateExperimentObjectList[key].avg.OD.dataVec+replicateExperimentObjectList[key].std.OD.dataVec,replicateExperimentObjectList[key].avg.OD.dataVec-replicateExperimentObjectList[key].std.OD.dataVec,facecolor=colors[colorIndex],alpha=0.1)
                ylabel = 'OD600'
            else:
                yData = replicateExperimentObjectList[key].avg.products[product].dataVec
                handle[key] = plt.errorbar(replicateExperimentObjectList[key].t,replicateExperimentObjectList[key].avg.products[product].dataVec,replicateExperimentObjectList[key].std.products[product].dataVec,lw=2.5,elinewidth=1,capsize=2,fmt='o-',color=colors[colorIndex])
                ylabel = product+" Titer (g/L)"

            colorIndex += 1

        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        ymin, ymax = plt.ylim()
        plt.ylim([0,ymax])
        plt.tight_layout()
        plt.tick_params(right="off",top="off")

    if len(titersToPlot) == 1:
        plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0)
        plt.subplots_adjust(right=0.7)
    if len(titersToPlot) > 1:
        plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.15, 0.5), loc=6, borderaxespad=0)
        plt.subplots_adjust(right=0.75)
    if len(titersToPlot) > 4:
        raise Exception("Unimplemented functionality")

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


#### Depricated Functions
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

def printTimeCourseOD(replicateExperimentObjectList, strainsToPlot):
    # You typically want your plot to be ~1.33x wider than tall. This plot is a rare
    # exception because of the number of lines being plotted on it.
    # Common sizes: (10, 7.5) and (12, 9)
    plt.figure(figsize=(12, 6))

    handle = dict()
    colors = plt.get_cmap('Set3')(np.linspace(0,1,len(strainsToPlot)))

    pltNum = 0

    pltNum += 1
    ax = plt.subplot(111)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    colorIndex = 0
    for key in strainsToPlot:
        scaledTime = np.divide(replicateExperimentObjectList[key].t,3600)
        handle[key] = plt.errorbar(scaledTime,replicateExperimentObjectList[key].avg.OD.dataVec,replicateExperimentObjectList[key].std.OD.dataVec,lw=2.5,elinewidth=1,capsize=2,fmt='o-',color=colors[colorIndex])
        # handle[key] = plt.errorbar(replicateExperimentObjectList[key].t,replicateExperimentObjectList[key].avg.OD.dataVec,lw=2.5,fmt='-o',color=colors[colorIndex])
        # handle[key] = plt.plot(np.linspace(min(scaledTime),max(scaledTime),50),
        #                                    replicateExperimentObjectList[key].avg.OD.returnCurveFitPoints(np.linspace(min(scaledTime),max(scaledTime))),'-',lw=2.5,color=colors[colorIndex])
        plt.fill_between(scaledTime,replicateExperimentObjectList[key].avg.OD.dataVec+replicateExperimentObjectList[key].std.OD.dataVec,replicateExperimentObjectList[key].avg.OD.dataVec-replicateExperimentObjectList[key].std.OD.dataVec,facecolor=colors[colorIndex],alpha=0.1)
        colorIndex += 1
    plt.xlabel("Time (hours)")
    plt.ylabel("OD600")
    ymin, ymax = plt.ylim()
    plt.ylim([0,ymax])
    plt.tight_layout()
    plt.tick_params(right="off",top="off")
    #plt.subplot(1,4,4)
    plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0)
    plt.subplots_adjust(right=0.7)