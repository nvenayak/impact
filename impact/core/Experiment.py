import sqlite3 as sql
import time

from .AnalyteData import TimeCourse, Biomass, Product, Substrate, Reporter
from .ReplicateTrial import ReplicateTrial
from .SingleTrial import SingleTrial

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
from sqlalchemy import Column, Integer, ForeignKey, Float, Date, String, event
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection


class Experiment(Base):
    __tablename__ = 'experiment'

    id = Column(Integer, primary_key=True)
    # replicate_trials = relationship('ReplicateTrial')
    stages = relationship('Stage',collection_class=attribute_mapped_collection('stage_id'),back_populates='parent')
    replicate_trial_dict = relationship('ReplicateTrial',
                                        collection_class=attribute_mapped_collection('unique_id'),
                                        back_populates='parent')
    import_date = Column(Date)
    start_date = Column(Date)
    end_date = Column(Date)
    title = Column(String)
    scientist_1 = Column(String)
    scientist_2 = Column(String)
    notes = Column(String)

    type = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': 'experiment',
        'polymorphic_on'      : type
    }

    def __init__(self, **kwargs):
        for key in kwargs:
            if key in ['import_date', 'start_date', 'end_date', 'title', 'scientist_1', 'scientist_2', 'notes']:
                setattr(self, key, kwargs[key])
        self.blank_reps = []
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

            return tabulate(data, headers=['strain', 'media', 'environment', 'analytes'])

    def __add__(self, experiment):
        """
        Add the experiments together by breaking them down to the analyte data and rebuilding to experiments.

        Parameters
        ----------
        experiment
        """
        from ..parsers import parse_analyte_data

        # Break the experiment into its base analytes
        analyte_list = []
        for replicate in list(self.replicate_trial_dict.values()) + list(experiment.replicate_trial_dict.values()):
            for singleTrial in replicate.single_trial_dict.values():
                for analyte in singleTrial.analyte_dict.values():
                    analyte_list.append(analyte)

        combined_experiment = Experiment()
        for attr in ['title', 'scientist_1', 'scientist_2', 'notes',
                     'import_date', 'start_date', 'end_date']:
            setattr(combined_experiment, attr, getattr(self, attr))
        # combined_experiment.info = self.info
        combined_replicates = parse_analyte_data(analyte_list)

        for replicate in combined_replicates:
            combined_experiment.add_replicate_trial(replicate)

        return combined_experiment

    @property
    def strains(self):
        return [str(replicate) for replicate in self.replicate_trial_dict.values()]

    @property
    def analyte_names(self):
        return list(set([analyte for rep in self.replicate_trial_dict.values()
                         for st in rep.single_trial_dict.values()
                         for analyte in st.analyte_dict.keys()]))
    @property
    def replicate_trials(self):
        return list(self.replicate_trial_dict.values())

    def calculate(self):
        t0 = time.time()
        print('Analyzing data...', end='')

        # Precalculate the blank stats, otherwise they won't be available for subtraction
        self.set_blanks()
        if self.blank_reps:
            for replicate in self.blank_reps:
                self.replicate_trial_dict[replicate.unique_id].calculate()
                if self.stages:
                    for repstage in self.stages.values():
                        repstage.calculate()

        for replicate_key in [replicate_key for replicate_key in self.replicate_trial_dict if
                              replicate_key not in self.blank_reps]:
            self.replicate_trial_dict[replicate_key].calculate()
            if self.stages:
                for repstage in self.stages.values():
                    repstage.calculate()
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

    # @event.listens_for(ReplicateTrial, 'load')
    def add_replicate_trial(self, replicateTrial):
        """
        Add a :class:`~ReplicateTrial` to the experiment.

        Parameters
        ----------
        replicateTrial : :class:`~ReplicateTrial`
        """
        replicateTrial.parent = self
        self.replicate_trial_dict[replicateTrial.trial_identifier.unique_replicate_trial()] = replicateTrial

    def parse_raw_data(self, *args, **kwargs):
        """
        Wrapper for parsing data into an experiment

        Parameters
        ----------
        args
        kwargs

        """
        from ..parsers import parse_raw_data
        parse_raw_data(experiment=self, *args, **kwargs)

    def set_blanks(self, mode='auto'):
        """
        Define how to associate blanks and perform blank subtraction.
        Parameters
        ----------
        mode (str) : how to determine blanks
        common_id (str) : which identifier to use

        NEW BLANKS DEFINITION.
        Previously, a 'common_id' was used as an identifier to figure out blanks for each replicate
        Blanks only need to be media dependent. This definition of blanks assigns a blank to a replicate trial
        if the media are the same. If not, it calculates the number of common components and assigns the blank with
        the most number of common components to that particular media. It is however good practice to have blanks
        for each media used.

        """


        self.blank_reps = [rep for rep in self.replicate_trial_dict.values()
                           if rep.trial_identifier.strain.name
                           in ['Blank', 'blank']]

        if self.blank_reps:

            blank_ids = {getattr(rep.trial_identifier, 'media'): rep
                             for rep in self.blank_reps}

            for rep in [rep for rep in self.replicate_trial_dict.values()
                        if rep not in self.blank_reps]:
                temp_media=rep.trial_identifier.media
                if (temp_media in blank_ids.keys()):
                    rep.set_blank(blank_ids[temp_media])
                else:
                    common_components={}
                    for i,blankmedia in enumerate(blank_ids):
                        common_components[blankmedia]=0
                        if blankmedia.parent.name==temp_media.parent.name:
                            common_components[blankmedia]+=1
                        common_components[blankmedia]+=len(set(blankmedia.components.keys())&set(temp_media.components.keys()))
                    rep.set_blank(blank_ids[max(common_components,key=common_components.get)])
            if mode == 'auto':
                pass
            else:
                raise Exception('Unimplemented')
        else:
            print("No blanks were indicated. Blank subtraction will not be done.")

    def set_stages(self, stage_indices=None):
        """
        Set the stages for the experiment. These stages can be defined manually based on growth kinetics
        or batch condition changes such as inducer additions.

        Parameters
        ----------
        stage_times -----> Removed because indices in pandas are the time values
        stage_indices

        """
        from .settings import settings
        live_calculations = settings.live_calculations


        self.stage_indices = stage_indices
        for stage_tuple in stage_indices:
            stage = Stage()
            stage.start_time = stage_tuple[0]
            stage.end_time = stage_tuple[1]
            stage.stage_id = str(stage.start_time)+'-'+str(stage.end_time)
            for replicate in self.replicate_trial_dict.values():
                stage.add_replicate_trial(replicate.create_stage(stage_tuple))
            self.stages[stage.stage_id] = stage

        if live_calculations:
            for replicate_key in self.replicate_trial_dict:
                replicate = self.replicate_trial_dict[replicate_key]
                replicate.calculate_stages()


class Stage(Experiment):
    __tablename__ = 'stage'

    parent_id = Column(Integer, ForeignKey('experiment.id'), primary_key=True)
    start_time = Column(Float)
    end_time = Column(Float)
    stage_id = Column(String)
    parent = relationship('Experiment',back_populates='stages')
    # parent_id = Column(Integer, ForeignKey('experiment.id'))

    __mapper_args__ = {
        'polymorphic_identity': 'experiment_stage',
    }
