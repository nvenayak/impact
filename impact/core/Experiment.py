import sqlite3 as sql
import time

from .AnalyteData import TimeCourse
from .ReplicateTrial import ReplicateTrial
from .SingleTrial import SingleTrial
from .. import parsers

try:
    from pyexcel_xlsx import get_data
except ImportError as e:
    print('Could not import pyexcel')
    print(e)
    pass

import matplotlib.pyplot as plt
import numpy as np

from warnings import warn

from ..database import Base
from sqlalchemy import Column, Integer, ForeignKey, Float, Date, String
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection




class Experiment(Base):
    __tablename__ = 'experiment'

    id = Column(Integer, primary_key=True)
    replicate_trials = relationship('ReplicateTrial')
    stages = relationship('Stage')
    replicate_trial_dict = relationship('ReplicateTrial',
                                        collection_class=attribute_mapped_collection('unique_id'))
    import_date = Column(Date)
    start_date = Column(Date)
    end_date = Column(Date)
    title = Column(String)
    scientist_1 = Column(String)
    scientist_2 = Column(String)
    notes = Column(String)

    def __init__(self, **kwargs):
        for key in kwargs:
            if key in ['import_date','start_date','end_date','title','scientist_1','scientist_2','notes']:
                setattr(self,key,kwargs[key])
        self.blank_key_list = []
        self.replicate_trial_dict = dict()
        self.stage_indices = []
        self.blank = None

        # self.info_keys = ['import_date', 'experiment_start_date', 'experiment_end_date', 'experiment_title',
        #                   'primary_scientist_name', 'secondary_scientist_name', 'medium_base', 'medium_supplements',
        #                   'notes']
        # if info is not None:
        #     self.info = {key: info[key] for key in self.info_keys if key in info}
        # else:
        #     self.info = dict()

    def __str__(self):
        try:
            from tabulate import tabulate
        except:
            return '\n'.join(['Trials', '-----']
                             + sorted([str(rep.trial_identifier) for rep in self.replicate_trial_dict.values()])
                             + ['\n', 'Analytes', '-----']
                             + self.analyte_names)
        else:
            data = [[str(rep.trial_identifier.strain),
                     str(rep.trial_identifier.media),
                     str(rep.trial_identifier.environment),
                     str(rep.get_analytes())] for rep in sorted(self.replicate_trial_dict.values(),
                                                                key=lambda rep: str(rep.trial_identifier))]

            return tabulate(data, headers=['strain', 'media', 'environment','analytes'])

    def __add__(self, experiment):
        """
        Add the experiments together by breaking them down to the analyte data and rebuilding to experiments.

        Parameters
        ----------
        experiment
        """
        # Break the experiment into its base analytes
        analyte_list = []
        for replicate in list(self.replicate_trial_dict.values())+list(experiment.replicate_trial_dict.values()):
            for singleTrial in replicate.single_trial_dict.values():
                for analyte in singleTrial.analyte_dict.values():
                    analyte_list.append(analyte)

        combined_experiment = Experiment()
        for attr in ['title','scientist_1','scientist_2','notes',
                                                     'import_date','start_date','end_date']:
            setattr(combined_experiment,attr,getattr(self,attr))
        # combined_experiment.info = self.info
        combined_experiment.parse_titers(analyte_list)

        return combined_experiment

    @property
    def strains(self):
        return [str(replicate) for replicate in self.replicate_trial_dict.values()]

    @property
    def analyte_names(self):
        return list(set([analyte for rep in self.replicate_trial_dict.values()
                         for st in rep.single_trial_dict.values()
                         for analyte in st.analyte_dict.keys()]))


    def calculate(self):
        t0 = time.time()
        print('Analyzing data...',end='')

        # Precalculate the blank stats, otherwise they won't be available for subtraction
        if self.blank_key_list:
            for replicate_key in self.blank_key_list:
                self.replicate_trial_dict[replicate_key].calculate()
                if self.stage_indices:
                    self.replicate_trial_dict[replicate_key].calculate_stages(self.stage_indices)

        for replicate_key in [replicate_key for replicate_key in self.replicate_trial_dict if
                              replicate_key not in self.blank_key_list]:
            self.replicate_trial_dict[replicate_key].calculate()
            if self.stage_indices:
                self.replicate_trial_dict[replicate_key].calculate_stages(self.stage_indices)
        print("Ran analysis in %0.1fs\n" % ((time.time() - t0)))

    def data(self):
        data = []
        for replicate_key in self.replicate_trial_dict:
            data.append([replicate_key])
            single_trial = self.replicate_trial_dict[replicate_key].single_trial_dict[
                list(self.replicate_trial_dict[replicate_key].single_trial_dict.keys())[0]]
            for titer_key in single_trial.analyte_dict.keys():
                data.append([titer_key])

                data.append(['Time (hours)'] + list(
                    self.replicate_trial_dict[replicate_key].replicate_df[titer_key].index))
                for col in self.replicate_trial_dict[replicate_key].replicate_df[titer_key]:
                    data.append(['rep #'
                                 + str(col)]
                                + list(self.replicate_trial_dict[replicate_key].replicate_df[titer_key][col]))
                data.append(['Average'] + list(
                    self.replicate_trial_dict[replicate_key].avg.analyte_dict[titer_key].pd_series))
                data.append(['Std'] + list(
                    self.replicate_trial_dict[replicate_key].std.analyte_dict[titer_key].pd_series))

                # Add spacing between the titers
                data.append([])
            # Add spacing between the replicates
            data.append([])
            data.append([])

        # Remove the last three rows which will be excess if it is the last row to be written
        del data[-1]
        del data[-1]
        del data[-1]

        return data

    def summary(self, level=None):
        for replicate_key in self.replicate_trial_dict:
            self.replicate_trial_dict[replicate_key].summary()

    def add_replicate_trial(self, replicateTrial):
        """
        Add a :class:`~ReplicateTrial` to the experiment.

        Parameters
        ----------
        replicateTrial : :class:`~ReplicateTrial`
        """
        replicateTrial.parent = self
        self.replicate_trial_dict[replicateTrial.trial_identifier.unique_replicate_trial()] = replicateTrial


    ## Parsing

    def parse_raw_data(self, *args, **kwargs):
        from ..parsers import parse_raw_data
        return parse_raw_data(experiment=self, *args, **kwargs)
    # Dicts
    def parse_time_point_dict(self, time_point_list):
        print('Parsing time point list...',end='')
        t0 = time.time()
        analyte_dict = {}
        for timePoint in time_point_list:
            if timePoint.get_unique_timepoint_id() in analyte_dict:
                analyte_dict[timePoint.get_unique_timepoint_id()].add_timepoint(timePoint)
            else:
                analyte_dict[timePoint.get_unique_timepoint_id()] = TimeCourse()
                analyte_dict[timePoint.get_unique_timepoint_id()].add_timepoint(timePoint)

        tf = time.time()
        print("Parsed %i time points in %0.1fs" % (len(time_point_list), (tf - t0)))
        self.parse_single_trial_dict(analyte_dict)

    def parse_single_trial_dict(self, single_trial_dict):
        print('Parsing analyte list...',end='')
        t0 = time.time()
        replicate_trial_dict = {}
        count = 0
        for analyte_dictKey in single_trial_dict:
            count += 1
            if single_trial_dict[analyte_dictKey].trial_identifier.unique_single_trial() in replicate_trial_dict:
                replicate_trial_dict[
                    single_trial_dict[analyte_dictKey].trial_identifier.unique_single_trial()].add_analyte_data(
                    single_trial_dict[analyte_dictKey])
            else:
                replicate_trial_dict[
                    single_trial_dict[analyte_dictKey].trial_identifier.unique_single_trial()] = SingleTrial()
                replicate_trial_dict[
                    single_trial_dict[analyte_dictKey].trial_identifier.unique_single_trial()].add_analyte_data(
                    single_trial_dict[analyte_dictKey])
        tf = time.time()
        print("Parsed %i single trials in %0.1fms" % (len(replicate_trial_dict), (tf - t0) * 1000))
        self.parse_replicate_trials(replicate_trial_dict)

    def parse_replicate_trials(self, replicate_trial_dict):
        print('Parsing single trial object list...',end='')
        t0 = time.time()
        for key in replicate_trial_dict:
            flag = 0
            for key2 in self.replicate_trial_dict:
                if key2 == replicate_trial_dict[key].trial_identifier.unique_replicate_trial():
                    self.replicate_trial_dict[key2].add_replicate(replicate_trial_dict[key])
                    flag = 1
                    break
            if flag == 0:
                self.replicate_trial_dict[
                    replicate_trial_dict[key].trial_identifier.unique_replicate_trial()] = ReplicateTrial()
                self.replicate_trial_dict[
                    replicate_trial_dict[key].trial_identifier.unique_replicate_trial()].parent = self
                self.replicate_trial_dict[
                    replicate_trial_dict[key].trial_identifier.unique_replicate_trial()].add_replicate(
                    replicate_trial_dict[key])
        tf = time.time()
        print("Parsed %i replicates in %0.1fs" % (len(self.replicate_trial_dict), (tf - t0)))

    # Lists
    def parse_titers(self, titer_list):
        print('Parsing analyte list...',end='')
        t0 = time.time()

        uniques = list(set([titer.trial_identifier.unique_single_trial() for titer in titer_list]))

        single_trial_list = []
        for unique in uniques:
            single_trial = SingleTrial()
            for titer in titer_list:
                if titer.trial_identifier.unique_single_trial() == unique:
                    single_trial.add_analyte_data(titer)
            single_trial_list.append(single_trial)

        tf = time.time()
        print("Parsed %i analytes in %0.1fms" % (len(single_trial_list), (tf - t0) * 1000))

        self.parse_single_trial_list(single_trial_list)

    def parse_single_trial_list(self, single_trial_list):
        uniques = list(set([single_trial.trial_identifier.unique_replicate_trial() for single_trial in single_trial_list]))

        replicate_trial_list = []
        for unique in uniques:
            replicate_trial = ReplicateTrial()
            for single_trial in single_trial_list:
                if single_trial.trial_identifier.unique_replicate_trial() == unique:
                    replicate_trial.add_replicate(single_trial)
                    replicate_trial_list.append(replicate_trial)

        self.replicate_trial_dict = dict()
        for replicate_trial in replicate_trial_list:
            self.add_replicate_trial(replicate_trial)


    ## Analysis details
    def set_blanks(self, mode='auto', common_id='id_2'):

        self.blank_key_list = [replicate_key
                               for replicate_key in self.replicate_trial_dict
                               if self.replicate_trial_dict[replicate_key].trial_identifier.strain.nickname
                               in ['Blank', 'blank']]

        if common_id:
            blank_ids = {
            getattr(self.replicate_trial_dict[replicate_key].trial_identifier, common_id): replicate_key
            for replicate_key in self.blank_key_list}

        for replicate_key in [replicate_key for replicate_key in self.replicate_trial_dict if
                              replicate_key not in self.blank_key_list]:
            if common_id:
                self.replicate_trial_dict[replicate_key].set_blank(
                    self.replicate_trial_dict[
                        blank_ids[getattr(self.replicate_trial_dict[replicate_key].trial_identifier, common_id)]]
                )
            else:
                self.replicate_trial_dict[replicate_key].set_blank(
                    self.replicate_trial_dict[self.blank_key_list[0]])

        # for replicate_key in self.replicate_trial_dict:
        #     if self.replicate_trial_dict[replicate_key].trial_identifier.strain.name in ['Blank','blank']:
        #         blank_list.append(replicate_key)
        if mode == 'auto':
            pass
        else:
            raise Exception('Unimplemented')

    def set_stages(self, stage_indices=None, stage_times=None):
        """

        Parameters
        ----------
        stage_times
        stage_indices

        """
        from .settings import settings
        live_calculations = settings.live_calculations

        if all([stage_indices, stage_times]):
            raise Exception('Cannot define both stage_indices and stage_times')

        if stage_times:
            # Find the closest time that matches
            raise Exception('stage times not implemented')

        # self.stage_indices = stage_indices
        for stage_tuple in stage_indices:
            stage = Stage()
            stage.start_time = stage_tuple[0]
            stage.end_time = stage_tuple[1]
            for replicate in self.replicate_trial_dict.values():
                stage.add_replicate_trial(replicate.create_stage(stage_tuple))
            self.stages.append(stage)

        if live_calculations:
            for replicate_key in self.replicate_trial_dict:
                replicate = self.replicate_trial_dict[replicate_key]
                replicate.calculate_stages()


    ### Plotting - Deprecated
    def printGenericTimeCourse(self, figHandle=[], strainsToPlot=[], titersToPlot=[], removePointFraction=1,
                               shadeErrorRegion=False, showGrowthRates=True, plotCurveFit=True, output_type='iPython',
                               **kwargs):
        """
        Wrapper for impact.printGenericTimeCourse_plotly
        """
        if not strainsToPlot:
            strainsToPlot = [rep for rep in self.replicate_trial_dict.values()]

        # Plot all product titers if none specified TODO: Add an option to plot OD as well
        if not titersToPlot:
            titersToPlot = self.analyte_names

        replicateTrialList = [self.replicate_trial_dict[key] for key in strainsToPlot]

        from ..plotting import printGenericTimeCourse_plotly
        printGenericTimeCourse_plotly(replicateTrialList=replicateTrialList, titersToPlot=titersToPlot,
                                      output_type=output_type, **kwargs)

    def printGrowthRateBarChart(self, figHandle=[], strainsToPlot=[], sortBy='id_1'):
        """
        MPL plotting function, deprecated since 2016/06/14 due to switch to plotly
        """
        if not figHandle:
            figHandle = plt.figure(figsize=(9, 5))

        if not strainsToPlot:
            strainsToPlot = [key for key in self.replicate_trial_dict]

        # Sort the strains to plot to HELP ensure that things are in the same order
        # TODO should find a better way to ensure this is the case
        strainsToPlot.sort()

        # Clear the plot and set some aesthetics
        plt.cla()
        ax = plt.subplot(111)
        figHandle.set_facecolor('w')
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Find all the unique identifier based on which identifier to 'sortBy'
        uniques = list(
            set([getattr(self.replicate_trial_dict[key].trial_identifier, sortBy) for key in strainsToPlot]))
        uniques.sort()

        # Find max number of samples (in case they all aren't the same)
        maxSamples = 0
        for unique in uniques:
            if len([self.replicate_trial_dict[key].avg.OD.rate[1] for key in strainsToPlot if
                    getattr(self.replicate_trial_dict[key].trial_identifier, sortBy) == unique]) > maxSamples:
                maxSamples = len([self.replicate_trial_dict[key].avg.OD.rate[1] for key in strainsToPlot if
                                  getattr(self.replicate_trial_dict[key].trial_identifier, sortBy) == unique])
                maxIndex = unique

        barWidth = 0.9 / len(uniques)
        index = np.arange(maxSamples)
        colors = plt.get_cmap('Set2')(np.linspace(0, 1.0, len(uniques)))

        i = 0
        handle = dict()
        for unique in uniques:
            handle[unique] = plt.bar(index[0:len(
                [self.replicate_trial_dict[key].avg.OD.rate[1] for key in strainsToPlot if
                 getattr(self.replicate_trial_dict[key].trial_identifier, sortBy) == unique])],
                                     [self.replicate_trial_dict[key].avg.OD.rate[1] for key in strainsToPlot if
                                      getattr(self.replicate_trial_dict[key].trial_identifier, sortBy) == unique],
                                     barWidth, yerr=[self.replicate_trial_dict[key].std.OD.rate[1] for key in
                                                     strainsToPlot if
                                                     getattr(self.replicate_trial_dict[key].trial_identifier,
                                                             sortBy) == unique],
                                     color=colors[i], ecolor='k', capsize=5, error_kw=dict(elinewidth=1, capthick=1))
            i += 1
            index += barWidth

        ax.yaxis.set_ticks_position('left')
        ax.xaxis.set_ticks_position('bottom')
        plt.ylabel('Growth Rate ($\mu$, h$^{-1}$)')
        xticklabel = ''
        for attribute in ['strain', 'id_1', 'id_2']:
            if attribute != sortBy:
                xticklabel += attribute

        if 'strain' == sortBy:
            tempticks = [self.replicate_trial_dict[key].trial_identifier.id_1 + '+' +
                         self.replicate_trial_dict[key].trial_identifier.id_2 for key in strainsToPlot
                         if getattr(self.replicate_trial_dict[key].trial_identifier, sortBy) == maxIndex]
        if 'id_1' == sortBy:
            tempticks = [self.replicate_trial_dict[key].trial_identifier.strain.nickname + '+' +
                         self.replicate_trial_dict[key].trial_identifier.id_2 for key in strainsToPlot
                         if getattr(self.replicate_trial_dict[key].trial_identifier, sortBy) == maxIndex]
        if 'id_2' == sortBy:
            tempticks = [self.replicate_trial_dict[key].trial_identifier.strain.nickname + '+' +
                         self.replicate_trial_dict[key].trial_identifier.id_1 for key in strainsToPlot
                         if getattr(self.replicate_trial_dict[key].trial_identifier, sortBy) == maxIndex]
        tempticks.sort()

        plt.xticks(index - 0.4, tempticks, rotation='45', ha='right', va='top')
        plt.tight_layout()
        plt.subplots_adjust(right=0.75)
        # print([handle[key][0][0] for key in handle])
        plt.legend([handle[key][0] for key in uniques], uniques, bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0)
        # ax.hold(False)

        return figHandle

    def printEndPointYield(self, figHandle=[], strainsToPlot=[], titersToPlot=[], sortBy='id_2', withLegend=2):
        """
        MPL plotting function, deprecated since 2016/06/14 due to switch to plotly
        """
        if not figHandle:
            figHandle = plt.figure(figsize=(9, 5))

        if not strainsToPlot:
            strainsToPlot = self.get_strains()

        if not titersToPlot:
            titersToPlot = self.analyte_names

        # Clear the plot and set some aesthetics
        plt.cla()
        ax = plt.subplot(111)
        figHandle.set_facecolor('w')
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # uniques = list(set([getattr(self.replicate_trial_dict[key].ReplicateTrialIdentifier,sortBy) for key in strainsToPlot]))
        # uniques.sort()
        #
        # # Find max number of samples (in case they all aren't the same)
        # maxSamples = 0
        # for unique in uniques:
        #     if len([self.replicate_trial_dict[key].avg.OD.fit_params[1] for key in strainsToPlot if getattr(self.replicate_trial_dict[key].ReplicateTrialIdentifier,sortBy) == unique]) > maxSamples:
        #         maxSamples = len([self.replicate_trial_dict[key].avg.OD.fit_params[1] for key in strainsToPlot if getattr(self.replicate_trial_dict[key].ReplicateTrialIdentifier,sortBy) == unique])
        #         maxIndex = unique

        replicateExperimentObjectList = self.replicate_trial_dict
        handle = dict()
        colors = plt.get_cmap('Set2')(np.linspace(0, 1.0, len(strainsToPlot)))

        barWidth = 0.6
        pltNum = 0

        if withLegend == 2:
            # # First determine which items to separate plot by (titer/OD, strain, id1, id2)
            # # TODO implement this
            #
            # # Then determine which items to group the plot by



            for product in titersToPlot:
                uniques = list(set(
                    [getattr(self.replicate_trial_dict[key].trial_identifier, sortBy) for key in strainsToPlot]))
                uniques.sort()

                # Find max number of samples (in case they all aren't the same)
                maxSamples = 0
                for unique in uniques:
                    if len([self.replicate_trial_dict[key].avg.products[product] for key in strainsToPlot if
                            getattr(self.replicate_trial_dict[key].trial_identifier,
                                    sortBy) == unique]) > maxSamples:
                        # if len([self.replicate_trial_dict[key].avg.products[prodKey] for prodkey in self.replicate_trial_dict[key] for key in strainsToPlot if getattr(self.replicate_trial_dict[key].ReplicateTrialIdentifier,sortBy) == unique]) > maxSamples:
                        maxSamples = len(
                            [self.replicate_trial_dict[key].avg.products[product] for key in strainsToPlot if
                             getattr(self.replicate_trial_dict[key].trial_identifier, sortBy) == unique])
                        maxIndex = unique

                # Create empty arrays to store data
                endPointTiterAvg = []
                endPointTiterStd = []
                endPointTiterLabel = []

                # Choose plot number
                pltNum += 1
                ax = plt.subplot(1, len(titersToPlot), pltNum)

                # Initial variables and choose plotting locations of bars
                location = 0

                # Prepare data for plotting
                for key in strainsToPlot:
                    if getattr(self.replicate_trial_dict[key].trial_identifier, sortBy) == unique:
                        endPointTiterLabel.append(key)
                        endPointTiterAvg.append(replicateExperimentObjectList[key].avg.yields[product][-1])
                        endPointTiterStd.append(replicateExperimentObjectList[key].std.yields[product][-1])

                barWidth = 0.9 / len(uniques)
                index = np.arange(maxSamples)
                colors = plt.get_cmap('Set2')(np.linspace(0, 1.0, len(uniques)))

                i = 0
                for unique in uniques:
                    print([self.replicate_trial_dict[key].avg.yields[product][-1] for key in strainsToPlot if
                           getattr(self.replicate_trial_dict[key].trial_identifier, sortBy) == unique])
                    print(len(
                        [self.replicate_trial_dict[key].avg.yields[product][-1] for key in strainsToPlot if
                         getattr(self.replicate_trial_dict[key].trial_identifier, sortBy) == unique]))
                    print(
                        [getattr(self.replicate_trial_dict[key].trial_identifier, sortBy) for key in strainsToPlot
                         if getattr(self.replicate_trial_dict[key].trial_identifier, sortBy) == unique])
                    print()
                    handle[unique] = plt.bar(index[0:len(
                        [self.replicate_trial_dict[key].avg.products[product] for key in strainsToPlot if
                         getattr(self.replicate_trial_dict[key].trial_identifier, sortBy) == unique])],
                                             [self.replicate_trial_dict[key].avg.yields[product][-1] for key in
                                              strainsToPlot if
                                              getattr(self.replicate_trial_dict[key].trial_identifier,
                                                      sortBy) == unique],
                                             barWidth,
                                             yerr=[self.replicate_trial_dict[key].std.yields[product][-1] for
                                                   key in strainsToPlot if
                                                   getattr(self.replicate_trial_dict[key].trial_identifier,
                                                           sortBy) == unique],
                                             color=colors[i], ecolor='k', capsize=5,
                                             error_kw=dict(elinewidth=1, capthick=1)
                                             )
                    index += barWidth
                    i += 1

                plt.ylabel(product + " Yield (g/g)")
                ymin, ymax = plt.ylim()
                plt.ylim([0, ymax])

                endPointTiterLabel.sort()

                xticklabel = ''
                for attribute in ['strain', 'id_1', 'id_2']:
                    if attribute != sortBy:
                        xticklabel += attribute

                if 'strain_id' == sortBy:
                    tempticks = [self.replicate_trial_dict[key].trial_identifier.id_1 + '+' +
                                 self.replicate_trial_dict[key].trial_identifier.id_2 for key in
                                 strainsToPlot
                                 if getattr(self.replicate_trial_dict[key].trial_identifier, sortBy) == maxIndex]
                if 'id_1' == sortBy:
                    tempticks = [self.replicate_trial_dict[key].trial_identifier.strain.nickname + '+' +
                                 self.replicate_trial_dict[key].trial_identifier.id_2 for key in
                                 strainsToPlot
                                 if getattr(self.replicate_trial_dict[key].trial_identifier, sortBy) == maxIndex]
                if 'id_2' == sortBy:
                    tempticks = [self.replicate_trial_dict[key].trial_identifier.strain.nickname + '+' +
                                 self.replicate_trial_dict[key].trial_identifier.id_1 for key in
                                 strainsToPlot
                                 if getattr(self.replicate_trial_dict[key].trial_identifier, sortBy) == maxIndex]
                tempticks.sort()

                plt.xticks(index - 0.4, tempticks, rotation='45', ha='right', va='top')

                ax.yaxis.set_ticks_position('left')
                ax.xaxis.set_ticks_position('bottom')
            figManager = plt.get_current_fig_manager()
            figManager.window.showMaximized()
            plt.tight_layout()
            plt.subplots_adjust(right=0.875)
            plt.legend([handle[key][0] for key in uniques], uniques, bbox_to_anchor=(1.05, 0.5), loc=6, borderaxespad=0)

        if withLegend == 0:
            plt.figure(figsize=(6, 3))
            for product in titersToPlot:
                endPointTiterAvg = []
                endPointTiterStd = []
                endPointTiterLabel = []
                pltNum += 1
                # ax = plt.subplot(0.8)
                ax = plt.subplot(1, len(
                    replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products), pltNum)
                ax.spines["top"].set_visible(False)
                # ax.spines["bottom"].set_visible(False)
                ax.spines["right"].set_visible(False)
                # ax.spines["left"].set_visible(False)
                location = 0
                index = np.arange(len(strainsToPlot))

                strainsToPlot.sort()

                for key in strainsToPlot:
                    endPointTiterLabel.append(key)
                    endPointTiterAvg.append(replicateExperimentObjectList[key].avg.yields[product][-1])
                    endPointTiterStd.append(replicateExperimentObjectList[key].std.yields[product][-1])

                handle[key] = plt.bar(index, endPointTiterAvg, barWidth, yerr=endPointTiterStd,
                                      color=plt.get_cmap('Set2')(0.25), ecolor='black', capsize=5,
                                      error_kw=dict(elinewidth=1, capthick=1))
                location += barWidth
                plt.xlabel("Time (hours)")
                plt.ylabel(product + " Yield (g/g)")
                ymin, ymax = plt.ylim()
                plt.ylim([0, ymax])
                plt.tight_layout()
                endPointTiterLabel.sort()
                plt.xticks(index + barWidth / 2, endPointTiterLabel, rotation='45', ha='right', va='top')
                ax.yaxis.set_ticks_position('left')
                ax.xaxis.set_ticks_position('bottom')

        if withLegend == 1:
            plt.figure(figsize=(6, 2))

            for product in replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products:
                endPointTiterAvg = []
                endPointTiterStd = []
                endPointTiterLabel = []
                pltNum += 1
                ax = plt.subplot(1, len(
                    replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products), pltNum)
                ax.spines["top"].set_visible(False)
                # ax.spines["bottom"].set_visible(False)
                ax.spines["right"].set_visible(False)
                # ax.spines["left"].set_visible(False)
                location = 0
                index = np.arange(len(strainsToPlot))

                for key in strainsToPlot:
                    endPointTiterLabel.append(key)
                    endPointTiterAvg.append(replicateExperimentObjectList[key].avg.yields[product][-1])
                    endPointTiterStd.append(replicateExperimentObjectList[key].std.yields[product][-1])

                barList = plt.bar(index, endPointTiterAvg, barWidth, yerr=endPointTiterStd, ecolor='k')
                count = 0
                for bar, count in zip(barList, range(len(strainsToPlot))):
                    bar.set_color(colors[count])
                location += barWidth
                plt.ylabel(product + " AnalyteData (g/L)")
                ymin, ymax = plt.ylim()
                plt.ylim([0, ymax])
                plt.tight_layout()
                plt.xticks([])
                ax.yaxis.set_ticks_position('left')
                ax.xaxis.set_ticks_position('bottom')
            plt.subplots_adjust(right=0.7)
            plt.legend(barList, strainsToPlot, bbox_to_anchor=(1.15, 0.5), loc=6, borderaxespad=0)

    def printYieldTimeCourse(self, strainsToPlot):
        """
        MPL plotting function, deprecated since 2016/06/14 due to switch to plotly
        """
        replicateExperimentObjectList = self.replicate_trial_dict
        # You typically want your plot to be ~1.33x wider than tall. This plot is a rare
        # exception because of the number of lines being plotted on it.
        # Common sizes: (10, 7.5) and (12, 9)
        plt.figure(figsize=(12, 3))

        handle = dict()
        barWidth = 0.9 / len(strainsToPlot)
        # plt.hold(False)
        pltNum = 0
        colors = plt.get_cmap('Paired')(np.linspace(0, 1.0, len(strainsToPlot)))
        for product in replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products:
            pltNum += 1
            ax = plt.subplot(1, len(
                replicateExperimentObjectList[list(replicateExperimentObjectList.keys())[0]].avg.products) + 1, pltNum)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            location = 0
            colorIndex = 0
            for key in strainsToPlot:
                index = np.arange(len(replicateExperimentObjectList[key].t))
                handle[key] = plt.bar(index + location, replicateExperimentObjectList[key].avg.yields[product],
                                      barWidth, yerr=replicateExperimentObjectList[key].std.yields[product],
                                      color=colors[colorIndex], ecolor='k')
                plt.xticks(index + barWidth, replicateExperimentObjectList[key].t)
                location += barWidth
                colorIndex += 1
                # print(replicateExperimentObjectList[key].avg.products[product].fit_params)
                # handle[key] = plt.plot(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50),
                #                                    replicateExperimentObjectList[key].avg.products[product].data_curve_fit(np.linspace(min(replicateExperimentObjectList[key].t),max(replicateExperimentObjectList[key].t),50)),'-',lw=2.5)
            plt.xlabel("Time (hours)")
            plt.ylabel(product + " Yield (g/g)")
            ymin, ymax = plt.ylim()
            plt.ylim([0, 1])
            plt.tight_layout()
        # plt.subplot(1,4,4)
        plt.legend([handle[key] for key in handle], [key for key in handle], bbox_to_anchor=(1.15, 0.5), loc=6,
                   borderaxespad=0)
        plt.subplots_adjust(right=1.05)

    def printAllReplicateTimeCourse(self, figHandle=[], strainToPlot=[]):

        if not figHandle:
            figHandle = plt.figure(figsize=(9, 5))

        plt.clf()
        if len(strainToPlot) > 1:
            strainToPlot = self.get_strains()[0]
        for singleExperiment in self.replicate_trial_dict[strainToPlot[0]].single_trial_list:
            plt.plot(singleExperiment.OD.time_vector, singleExperiment.OD.data_vector)
        plt.ylabel(singleExperiment.trial_identifier.unique_replicate_trial())

class Stage(Experiment):
    __tablename__ = 'stage'

    id = Column(Integer, primary_key=True)
    start_time = Column(Float)
    end_time = Column(Float)

    parent = relationship('Experiment')
    parent_id = Column(Integer, ForeignKey('experiment.id'))