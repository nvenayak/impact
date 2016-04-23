__author__ = 'Naveen'

import numpy as np
import matplotlib.pyplot as plt
import time

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
                removePointFraction = 6

                scaledTime = replicateExperimentObjectList[key].t
                handle[key] = plt.plot(np.linspace(min(scaledTime),max(scaledTime),50),
                                        replicateExperimentObjectList[key].avg.OD.returnCurveFitPoints(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50)),'-',lw=1.5,color=colors[colorIndex])
                handle[key] = plt.errorbar(scaledTime[::removePointFraction],replicateExperimentObjectList[key].avg.OD.dataVec[::removePointFraction],replicateExperimentObjectList[key].std.OD.dataVec[::removePointFraction],lw=2.5,elinewidth=1,capsize=2,fmt='o',markersize=5,color=colors[colorIndex])

                plt.fill_between(scaledTime,replicateExperimentObjectList[key].avg.OD.dataVec+replicateExperimentObjectList[key].std.OD.dataVec,
                                 replicateExperimentObjectList[key].avg.OD.dataVec-replicateExperimentObjectList[key].std.OD.dataVec,
                                 facecolor=colors[colorIndex],alpha=0.1)
                print(scaledTime[-1]+0.5,
                         replicateExperimentObjectList[key].avg.OD.returnCurveFitPoints(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50))[-1],
                         '$\mu$ = '+'{:.2f}'.format(replicateExperimentObjectList[key].avg.OD.rate[1]) + ' $\pm$ ' + '{:.2f}'.format(replicateExperimentObjectList[key].std.OD.rate[1]))

                plt.text(scaledTime[-1]+0.5,
                         replicateExperimentObjectList[key].avg.OD.returnCurveFitPoints(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50))[-1],
                         '$\mu$ = '+'{:.2f}'.format(replicateExperimentObjectList[key].avg.OD.rate[1]) + ' $\pm$ ' + '{:.2f}'.format(replicateExperimentObjectList[key].std.OD.rate[1]),
                         verticalalignment='center')
                ylabel = 'OD600'
            else:
                yData = replicateExperimentObjectList[key].avg.products[product].dataVec
                handle[key] = plt.errorbar(replicateExperimentObjectList[key].t,replicateExperimentObjectList[key].avg.products[product].dataVec,replicateExperimentObjectList[key].std.products[product].dataVec,lw=2.5,elinewidth=1,capsize=2,fmt='o-',color=colors[colorIndex])
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
        raise Exception("Unimplemented functionality")

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
                #if getattr(replicateExperimentObjectList[key].RunIdentifier,sortBy) == maxIndex],
               rotation='45', ha='right', va='top')
    plt.tight_layout()
    plt.subplots_adjust(right=0.75)
    #print([handle[key][0][0] for key in handle])
    plt.legend([handle[key][0] for key in uniques],uniques,bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0)

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
            # print(replicateExperimentObjectList[key].avg.products[product].rate)
            # print(replicateExperimentObjectList[key].avg.products[product].returnCurveFitPoints(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50)))
            handle[key] = plt.plot(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50),
                                               replicateExperimentObjectList[key].avg.products[product].returnCurveFitPoints(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50)),'-',lw=2.5,color=colors[colorIndex])
            handle[key] = plt.errorbar(replicateExperimentObjectList[key].t,replicateExperimentObjectList[key].avg.products[product].dataVec,replicateExperimentObjectList[key].std.products[product].dataVec,lw=2.5,elinewidth=1,capsize=2,fmt='o',color=colors[colorIndex])
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
    removePointFraction = 6
    maxTextLabelHeight = 0
    for key in strainsToPlot:
        scaledTime = replicateExperimentObjectList[key].t
        #handle[key] = plt.errorbar(replicateExperimentObjectList[key].t,replicateExperimentObjectList[key].avg.OD.dataVec,lw=2.5,fmt='-o',color=colors[colorIndex])
        #print(replicateExperimentObjectList[key].avg.OD.returnCurveFitPoints(np.linspace(min(scaledTime),max(scaledTime),50)))
        handle[key] = plt.plot(np.linspace(min(scaledTime),max(scaledTime),50),
                                           replicateExperimentObjectList[key].avg.OD.returnCurveFitPoints(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50)),'-',lw=1.5,color=colors[colorIndex])
        handle[key] = plt.errorbar(scaledTime[::removePointFraction],replicateExperimentObjectList[key].avg.OD.dataVec[::removePointFraction],replicateExperimentObjectList[key].std.OD.dataVec[::removePointFraction],lw=2.5,elinewidth=1,capsize=2,fmt='o',markersize=5,color=colors[colorIndex])
        plt.fill_between(scaledTime,replicateExperimentObjectList[key].avg.OD.dataVec+replicateExperimentObjectList[key].std.OD.dataVec,replicateExperimentObjectList[key].avg.OD.dataVec-replicateExperimentObjectList[key].std.OD.dataVec,facecolor=colors[colorIndex],alpha=0.1)
        colorIndex += 1
        plt.text(scaledTime[-1]+0.5, replicateExperimentObjectList[key].avg.OD.returnCurveFitPoints(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50))[-1],'$\mu$ = '+'{:.2f}'.format(replicateExperimentObjectList[key].avg.OD.rate[1]) + ' $\pm$ ' + '{:.2f}'.format(replicateExperimentObjectList[key].std.OD.rate[1]), verticalalignment='center')
        #print(scaledTime[-1]+0.5, replicateExperimentObjectList[key].avg.OD.returnCurveFitPoints(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50))[-1],'$\mu$ = '+'{:.2f}'.format(replicateExperimentObjectList[key].avg.OD.rate[1]) + ' $\pm$ ' + '{:.2f}'.format(replicateExperimentObjectList[key].std.OD.rate[1]),replicateExperimentObjectList[key].avg.OD.rate[0]," ",replicateExperimentObjectList[key].avg.OD.rate[1]," ",replicateExperimentObjectList[key].avg.OD.rate[2]," ",replicateExperimentObjectList[key].avg.OD.rate[3]," ",replicateExperimentObjectList[key].avg.OD.rate[4]," ",replicateExperimentObjectList[key].avg.OD.rate[5])
        # if replicateExperimentObjectList[key].avg.OD.returnCurveFitPoints(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50))[-1] > maxTextLabelHeight:
        #     maxTextLabelHeight = replicateExperimentObjectList[key].avg.OD.returnCurveFitPoints(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50))[-1]
        #print(maxTextLabelHeight)
    #plt.text(scaledTime[-1]+0.5,maxTextLabelHeight+0.01,'$\mu$',horizontalalignment = 'center', verticalalignment = 'center', fontsize=14)
    plt.xlabel("Time (hours)")
    plt.ylabel("OD600")
    ymin, ymax = plt.ylim()
    xmin, xmax = plt.xlim()
    plt.ylim([0,ymax])
    plt.xlim([0,xmax*1.2])
    plt.tight_layout()
    plt.tick_params(right="off",top="off")
    #plt.subplot(1,4,4)
    plt.legend([handle[key] for key in handle],[key for key in handle],bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0, frameon=False)
    plt.subplots_adjust(right=0.7)
    plt.savefig('Figures/'+time.strftime('%y')+'.'+time.strftime('%m')+'.'+time.strftime('%d')+" H"+time.strftime('%H')+'-M'+time.strftime('%M')+'-S'+time.strftime('%S')+'.png')

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