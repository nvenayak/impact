# coding=utf-8

from .TrialIdentifier import TrialIdentifier, Strain, Media

from ..curve_fitting import *

import pandas as pd
import dill as pickle

from scipy.signal import savgol_filter

# from django.db import models
# from .database import PandasField, JSONSerializableField

from ..database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, PickleType, Float
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import event

class AnalyteData(object):
    # class Meta:
    #     app_label = 'impact'
    # __tablename__ = 'analyte_data'
    # id = Column(Integer,primary_key=True)
    # trial_identifier = relationship(TrialIdentifier)

    def __init__(self):
        self.timePointList = []
        self._trial_identifier = TrialIdentifier()

        # self.strain =
        # self.media =
        # self.generic_id_1 =
        # self.generic_id_2 =
        # self.generic_id_3 =

    @property
    def trial_identifier(self):
        return self._trial_identifier

    @trial_identifier.setter
    def trial_identifier(self, trial_identifier):
        self._trial_identifier = trial_identifier

    def add_timepoint(self, timePoint):
        raise (Exception("No addTimePoint method defined in the child"))

    def getTimeCourseID(self):
        if len(self.timePointList) > 0:
            return ''.join([str(getattr(self.timePointList[0].trial_identifier,attr))
                            for attr in ['strain_id','id_1','id_2','replicate_id']])
        elif self.trial_identifier.strain_id != '':
            return self.trial_identifier.strain_id + \
                   self.trial_identifier.id_1 + \
                   self.trial_identifier.id_2 + \
                   str(self.trial_identifier.replicate_id)
        else:
            raise Exception("No unique ID or time points in AnalyteData")

    def getReplicateID(self):
        return self.trial_identifier.strain_id + self.trial_identifier.id_1 + self.trial_identifier.id_2

# class TimeDataTuple(Base):
#     __tablename__ = 'time_data_pair'
#     time = 0.
#     data = 0.
#
# class Array(Base):
#     array = ForeignKey(Integer,'time_data_tuple')

class FitParameter(Base):
    __tablename__ = 'fit_parameters'

    id = Column(Integer,primary_key = True)
    parent = Column(Integer,ForeignKey('time_course.id'))
    parameter_name = Column(String)
    parameter_value = Column(Float)

    def __init__(self, name, value):
        self.parameter_name = name
        self.parameter_value = value

class TimePoint(Base):
    __tablename__ = 'time_point'

    id = Column(Integer, primary_key=True)
    trial_identifier_id = Column(Integer,ForeignKey('trial_identifier.id'))
    trial_identifier = relationship('TrialIdentifier')
    time = Column(Float)
    data = Column(Float)
    parent_id = Column(Integer,ForeignKey('time_course.id'))
    parent = relationship('TimeCourse')
    # gradient_id = ForeignKey('TimeCourse.id')

    def __init__(self, trial_identifier = TrialIdentifier(), time=None, data=None):
        self.trial_identifier = trial_identifier
        self.time = time
        self.data = data
        self.units = {'t'    : 'h',
                      'titer': 'g'}

    def get_unique_timepoint_id(self):
        return self.trial_identifier.strain_id + self.trial_identifier.id_1 + self.trial_identifier.id_2 + str(
            self.trial_identifier.replicate_id) + self.trial_identifier.analyte_name

class TimeCourse(AnalyteData, Base):
    """
    Child of :class:`~AnalyteData` which contains curve fitting relevant to time course data
    """
    # class Meta:
    #     app_label = 'impact'
    #
    # parent = models.ForeignKey('impact.SingleTrial', on_delete=models.CASCADE, blank=True, null=True)
    # calculations_uptodate = models.BooleanField()
    # pd_series = PandasField()
    # fit_params = JSONSerializableField()
    # gradient = JSONSerializableField()
    # specific_productivity = JSONSerializableField()
    # stages = models.ManyToManyField('self')

    __tablename__ = 'time_course'

    discriminator = Column(String(50))
    __mapper_args__ = {'polymorphic_on': discriminator}

    id = Column(Integer,primary_key = True)

    trial_identifier_id = Column(Integer, ForeignKey('trial_identifier.id'))
    _trial_identifier = relationship('TrialIdentifier')
    time_points = relationship('TimePoint')
    gradient_points = relationship('TimePoint')
    calculations_uptodate = Column(Boolean)
    fit_params = relationship('FitParameter',
                              collection_class=attribute_mapped_collection('keyword'),
                              cascade="all, delete-orphan") # Column(PickleType())

    # pd_series = Column(PickleType)
    # gradient = Column(PickleType)
    # specific_productivity = Column(PickleType)

    stage_parent_id = Column(Integer, ForeignKey('time_course.id'))
    stages = relationship('TimeCourse')

    parent_id = Column(Integer, ForeignKey('single_trial.id'))
    parent = relationship('SingleTrial')

    def __init__(self, **kwargs):
        # Get the default parameters
        from .settings import settings

        remove_death_phase_flag = settings.remove_death_phase_flag
        use_filtered_data = settings.use_filtered_data
        minimum_points_for_curve_fit = settings.minimum_points_for_curve_fit
        savgolFilterWindowSize = settings.savgolFilterWindowSize

        # Overwrite user-set parameters
        for arg in kwargs:
            setattr(self,arg,kwargs[arg])

        # Parent constructor
        AnalyteData.__init__(self)

        # Used to store the single_trial to which each analyte instance belongs
        self.parent = None  # type SingleTrial

        # Keep track of whether or not calculations need to be updated
        self.calculations_uptodate = False

        self.pd_series = None
        self._time_vector = None    # Not stored in db
        self.time_vector = None # Error thrown if deleted, # Not stored in db
        self._data_vector = None    # Not stored in db
        self.pd_series = None


        self.fit_params = dict()
        # self.units = {'time': 'hours',
        #               'data': 'None'}

        self.gradient = []
        self._specific_productivity = None

        # Options
        self.removeDeathPhaseFlag = remove_death_phase_flag
        self.useFilteredDataFlag = use_filtered_data
        self.minimum_points_for_curve_fit = minimum_points_for_curve_fit
        self.savgolFilterWindowSize = savgolFilterWindowSize

        self.deathPhaseStart = None
        self.blankSubtractionFlag = True

        self.stages = []
        self._stage_indices = None

        # Declare the default curve fit
        self.fit_type = 'gompertz'

    def serialize(self):
        serialized_dict = {}
        # serialized_dict['time_vector'] = self.time_vector
        # serialized_dict['data_vector'] = self.data_vector
        serialized_dict['data'] = self.pd_series.to_json()
        serialized_dict['fit_params'] = self.fit_params
        serialized_dict['gradient'] = list(self.gradient)

        try:
            serialized_dict['specific_productivity'] = list(self.specific_productivity)
        except Exception as e:
            print(e)

        serialized_dict['analyte_name'] = self.trial_identifier.analyte_name
        serialized_dict['analyte_type'] = self.trial_identifier.analyte_type

        options = {}
        for option in ['removeDeathPhaseFlag', 'useFilteredDataFlag', 'minimum_points_for_curve_fit']:
            options[option] = getattr(self,option)
        serialized_dict['options'] = options

        return serialized_dict

    @property
    def specific_productivity(self):
        if self._specific_productivity is None:
            if not self.parent:
                raise Exception('Cannot calculate productivity automatically because no parent single_trial '
                                'is defined')
            self.parent.calculate_specific_productivity()
            return self._specific_productivity
        else:
            return self._specific_productivity

    @specific_productivity.setter
    def specific_productivity(self, specific_productivity):
        self._specific_productivity = specific_productivity

    @property
    def stage_indices(self):
        return self._stage_indices

    @stage_indices.setter
    def stage_indices(self, stage_indices):
        self._stage_indices = stage_indices
        for stage_bounds in stage_indices:
            self.stages.append(self.create_stage(stage_bounds))

    @hybrid_property
    def trial_identifier(self):
        return self._trial_identifier

    @AnalyteData.trial_identifier.setter
    def trial_identifier(self, trial_identifier):
        self._trial_identifier = trial_identifier

        if trial_identifier.analyte_type == 'product':
            self.fit_type = 'productionEquation_generalized_logistic'
        if trial_identifier.analyte_type == 'biomass':
            self.fit_type = 'janoschek'#'gompertz'#'richard_5','growthEquation_generalized_logistic'

    @property
    def time_vector(self):
        return self._time_vector

    @time_vector.setter
    def time_vector(self, time_vector):
        if self.pd_series is None:
            self.pd_series = pd.Series(index=time_vector)
        else:
            self.pd_series.index = time_vector

        self._time_vector = np.array(self.pd_series.index)

    @property
    def data_vector(self):
        self._data_vector = np.array(self.pd_series)

        if self.useFilteredDataFlag == True:
            return savgol_filter(self._data_vector, self.savgolFilterWindowSize, 3)
        else:
            return self._data_vector

    @data_vector.setter
    def data_vector(self, dataVec):
        from .settings import settings
        live_calculations = settings.live_calculations
        perform_curve_fit = settings.perform_curve_fit

        if self.pd_series is None:
            self.pd_series = pd.Series(dataVec)
        else:
            self.pd_series = pd.Series(dataVec,index=self.pd_series.index)

        # To maintain backwards compatability
        self._data_vector = np.array(self.pd_series)

        self.deathPhaseStart = len(dataVec)

        if live_calculations:   self.calculate()

    def calculate(self):
        from .settings import settings
        perform_curve_fit = settings.perform_curve_fit

        if self._time_vector is not None:
            self.gradient = np.gradient(self._data_vector) / np.gradient(self.time_vector)

        if self.removeDeathPhaseFlag:
            self.find_death_phase(self.data_vector)

        if len(self.data_vector) > self.minimum_points_for_curve_fit and perform_curve_fit:
            self.curve_fit_data()

    def find_death_phase(self, data_vector):
        self.deathPhaseStart = self.find_death_phase_static(data_vector,
                                                            use_filtered_data_flag = self.useFilteredDataFlag,
                                                            verbose = verbose)

    @staticmethod
    def find_death_phase_static(data_vector, use_filtered_data_flag=False, verbose=False, hyper_parameter = 1):
        # The hyper_parameter determines the number of points
        # which need to have a negative diff to consider it death phase

        death_phase_start = len(data_vector)

        # Check if there is a reasonable difference between the min and max of the curve
        if (np.max(data_vector) - np.min(data_vector)) / np.min(data_vector) > 2:
            if verbose: print('Growth range: ', (np.max(data_vector) - np.min(data_vector)) / np.min(data_vector))

            if use_filtered_data_flag:
                filteredData = savgol_filter(data_vector, 51, 3)
            else:
                filteredData = np.array(data_vector)
            diff = np.diff(filteredData)

            count = 0
            flag = 0

            for i in range(len(diff) - hyper_parameter):
                # Check if the diff is negative (e.g. death fit_params > growth fit_params)
                if diff[i] <= 0:
                    flag = 1
                    count += 1
                    if count > hyper_parameter:
                        death_phase_start = i - hyper_parameter
                        break
                elif count > 0:
                    # Reset counter if death_phase increases again
                    count = 1
                    flag = 0

        if death_phase_start == 0:
            death_phase_start = len(data_vector)

        return death_phase_start

    def db_commit(self, singleTrialID, c=None, stat=None):
        if stat is None:
            stat_prefix = ''
        else:
            stat_prefix = '_' + stat
        c.execute(
            """INSERT INTO timeCourseTable""" + stat_prefix + """(singleTrial""" + stat_prefix
            + """ID, titerType, analyte_name, time_vector, data_vector, fit_params) VALUES (?, ?, ?, ?, ?, ?)""",
            (singleTrialID, self.trial_identifier.analyte_type, self.trial_identifier.analyte_name,
             self.time_vector.dumps(), self.data_vector.dumps(), pickle.dumps(self.fit_params)))


    def summary(self, print=False):
        summary = dict()
        summary['time_vector'] = self.time_vector
        summary['data_vector'] = self.data_vector
        summary['number_of_data_points'] = len(self.time_vector)
        summary['trial_identifier'] = self.trial_identifier.summary(['strain_id', 'id_1', 'id_2',
                                                                'analyte_name', 'titerType', 'replicate_id'])

        if print:
            print(summary)

        return summary

    def create_stage(self, stage_bounds):
        stage = TimeCourse()
        stage.trial_identifier = self.trial_identifier
        stage.time_vector = self.time_vector[stage_bounds[0]:stage_bounds[1] + 1]
        stage.data_vector = self.data_vector[stage_bounds[0]:stage_bounds[1] + 1]
        if len(self.gradient) > 0:
            stage.gradient = self.gradient[stage_bounds[0]:stage_bounds[1] + 1]
        if self._specific_productivity is not None:
            # Set the private variable to prevent any calculations
            stage._specific_productivity = self._specific_productivity[stage_bounds[0]:stage_bounds[1] + 1]

        return stage

    def data_curve_fit(self, t):
        return curve_fit_dict[self.fit_type].growthEquation(np.array(t), **self.fit_params)

    @event.listens_for(TimePoint, 'load')
    def add_timepoint(self, timePoint):
        from .settings import settings
        live_calculations = settings.live_calculations

        self.timePointList.append(timePoint)

        if len(self.timePointList) == 1:
            self.trial_identifier = timePoint.trial_identifier
            self._time_vector = np.array([timePoint.time])
            self._data_vector = np.array([timePoint.data])
        else:
            if self.timePointList[-1].trial_identifier.get_unique_for_SingleTrial() \
                    != self.timePointList[-2].trial_identifier.get_unique_for_SingleTrial():
                raise Exception("trial_identifiers don't match within the timeCourse object")

            # Check if ordering is broken
            if self.timePointList[-1].time < self.timePointList[-2].time:
                self.timePointList.sort(key=lambda timePoint: timePoint.time)
                self._time_vector = np.array([timePoint.time for timePoint in self.timePointList])
                self._data_vector = np.array([timePoint.data for timePoint in self.timePointList])
            else:
                # Otherwise simply append
                self._time_vector = np.append(self._time_vector, timePoint.time)
                self._data_vector = np.append(self._data_vector, timePoint.data)

        if self.pd_series is None:
            self.pd_series = pd.Series()
        pd_timepoint = pd.Series([timePoint.data], index=[timePoint.time])
        self.pd_series = self.pd_series.append(pd_timepoint)
        timePoint.parent = self

        if len(self.timePointList) > 6 and live_calculations:
            self.gradient = np.gradient(self._data_vector) / np.gradient(self.time_vector)

            # self.data_vector = np.array([timePoint.titer for timePoint in self.timepoint_list])
            # pass
            # print('Skipping exponential fit_params calculation')
            # print(self._time_vector)
            # print(self._data_vector)
            #
            # print(self.pd_series)
            # print(self.pd_series.index)
            # self.curve_fit_data()

    def curve_fit_data(self):
        from .settings import settings
        verbose = settings.verbose

        if self.trial_identifier.analyte_type == 'titer' or self.trial_identifier.analyte_type in ['substrate', 'product']:
            pass
            print(
                'Curve fitting for titers unimplemented in restructured curve fitting. Please see Depricated\depicratedCurveFittingCode.py')
            # gmod.set_param_hint('A', value=np.min(self.data_vector))
            # gmod.set_param_hint('B',value=2)
            # gmod.set_param_hint('C', value=1, vary=False)
            # gmod.set_param_hint('Q', value=0.1)#, max = 10)
            # gmod.set_param_hint('K', value = max(self.data_vector))#, max=5)
            # gmod.set_param_hint('nu', value=1, vary=False)
        elif self.trial_identifier.analyte_type in ['biomass']:
            # from scipy.interpolate import InterpolatedUnivariateSpline
            # spl = InterpolatedUnivariateSpline(self.time_vector, self.data_vector)
            # spl.set_smoothing_factor(0.2)
            # spl_grad = np.gradient(spl(self.time_vector)) / np.gradient(self.time_vector)
            # self.fit_params['growth_rate'] = max(spl_grad)
            #
            # import matplotlib.pyplot as plt
            # plt.figure()
            # plt.plot(self.time_vector,self.data_vector,'o')
            # plt.plot(self.time_vector,spl(self.time_vector),lw=2)
            # plt.show()
            # return max(spl_grad)


            # print('DPS: ',self.deathPhaseStart)
            # print(self.data_vector)
            # print(self.time_vector[0:self.deathPhaseStart])
            # print(self.data_vector[0:self.deathPhaseStart])
            if verbose: print('Started fit')
            # print(self.fit_type)
            if verbose: print('Death phase start: ',self.deathPhaseStart)
            result = curve_fit_dict[self.fit_type].calcFit(self.time_vector[0:self.deathPhaseStart],
                                                                    self.data_vector[0:self.deathPhaseStart])#,fit_kws = {'xatol':1E-10, 'fatol':1E-10})  # , fit_kws = {'maxfev': 20000, 'xtol': 1E-12, 'ftol': 1E-12})
            if verbose: print('Finished fit')
            # self.fit_params = [0, 0, 0, 0, 0, 0]
            for key in result.best_values:
                self.fit_params[key] = result.best_values[key]
            # print(result.fit_report())

            if verbose:
                import matplotlib.pyplot as plt
                plt.figure()
                plt.plot(self.time_vector[0:self.deathPhaseStart], self.data_vector[0:self.deathPhaseStart],         'bo')
                plt.plot(self.time_vector[0:self.deathPhaseStart], result.best_fit, 'r-')

            print(result.fit_report())
        else:
            print('Unidentified titer type:' + self.trial_identifier.analyte_type)
            print('Ensure that the trial identifier is described before adding data. This will allow curve fitting'
                  'to be appropriate to the analyte type.')

    def get_fit_parameters(self):
        return [[param['name'], self.fit_params[i]] for i, param in
                enumerate(curve_fit_dict[self.fit_type].paramList)]


# class TimeCourseStage(TimeCourse):
#     time_course = Column(Integer, ForeignKey('time_course.id'))
#
#     def __init__(self):
#         TimeCourse.__init__()

class TimeCourseShell(TimeCourse):
    """
    This is a shell of :class:`~AnalyteData` with an overidden setter to be used as a container
    """
    # class Meta:
    #     app_label = 'impact'

    # __mapper_args__ = {'polymorphic_identity': 'shell'}
    #
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    @TimeCourse.data_vector.setter
    def data_vector(self, dataVec):
        if self.pd_series is None:
            self.pd_series = pd.Series(dataVec)
        else:
            self.pd_series = pd.Series(dataVec,index=self.pd_series.index)

        # To maintain backwards compatability
        self._data_vector = np.array(self.pd_series)

class EndPoint(TimeCourse):
    """
    This is a child of :class:`~AnalyteData` which does not calcualte any time-based data
    """
    # class Meta:
    #     app_label = 'impact'
    # __tablename__ = 'endpoint'
    __mapper_args__ = {'polymorphic_identity': 'endpoint'}

    def __init__(self, runID, t, data):
        AnalyteData.__init__(self, runID, t, data)

    def add_timepoint(self, timePoint):
        if len(self.timePointList) < 2:
            self.timePointList.append(timePoint)
        else:
            raise Exception("Cannot have more than two timePoints for an endPoint Object")

        if len(self.timePointList) == 2:
            self.timePointList.sort(key=lambda timePoint: timePoint.time)

