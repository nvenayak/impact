# coding=utf-8

from .TrialIdentifier import ReplicateTrialIdentifier, Strain, Media

from ..curve_fitting import *

import pandas as pd

from scipy.signal import savgol_filter

from ..database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, PickleType, Float
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy import event


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

    time_point_type = Column(String)

    __mapper_args__ = {
        'polymorphic_on': time_point_type,
        'polymorphic_identity':'raw'
    }

    id = Column(Integer, primary_key=True)
    trial_identifier_id = Column(Integer,ForeignKey('time_course_identifier.id'))
    trial_identifier = relationship('TimeCourseIdentifier')
    time = Column(Float)
    data = Column(Float)
    parent_id = Column(Integer,ForeignKey('time_course.id'))
    parent = relationship('TimeCourse')

    use_in_analysis = Column(Boolean)

    def __init__(self, trial_identifier=None, time=None, data=None):
        self.trial_identifier = ReplicateTrialIdentifier() if trial_identifier is None else trial_identifier
        self.time = time
        self.data = data

    def get_unique_timepoint_id(self):
        return self.trial_identifier.unique_time_point()

            # str(self.trial_identifier.strain) + self.trial_identifier.id_1 + self.trial_identifier.id_2 + str(
            # self.trial_identifier.replicate_id) + self.trial_identifier.analyte_name


class GradientTimePoint(TimePoint):
    __mapper_args__ = {
        'polymorphic_identity':'gradient'
    }


class SpecificProductivityTimePoint(TimePoint):
    __mapper_args__ = {
        'polymorphic_identity':'specific_productivity'
    }


class TimeCourse(Base):
    """
    Child of :class:`~AnalyteData` which contains curve fitting relevant to time course data
    """
    __tablename__ = 'time_course'

    discriminator = Column(String(50))
    __mapper_args__ = {'polymorphic_on': discriminator}

    id = Column(Integer,primary_key = True)

    trial_identifier_id = Column(Integer, ForeignKey('time_course_identifier.id'))
    _trial_identifier = relationship('TimeCourseIdentifier')

    time_points = relationship('TimePoint')
    gradient_points = relationship('GradientTimePoint')
    specific_productivity_points = relationship('SpecificProductivityTimePoint')

    calculations_uptodate = Column(Boolean)
    fit_params = relationship('FitParameter',
                              collection_class=attribute_mapped_collection('parameter_name'),
                              cascade="all, delete-orphan")

    stages = relationship('TimeCourseStage')

    parent_id = Column(Integer, ForeignKey('single_trial.id'))
    parent = relationship('SingleTrial',uselist=False)

    analyte_name = Column(String)
    analyte_type = Column(String)

    def __init__(self, **kwargs):
        # Get the default parameters
        from .settings import settings

        remove_death_phase_flag = settings.remove_death_phase_flag
        use_filtered_data = settings.use_filtered_data
        minimum_points_for_curve_fit = settings.minimum_points_for_curve_fit
        savgolFilterWindowSize = settings.savgolFilterWindowSize

        if 'time_points' in kwargs:
            for time_point in kwargs['time_points']:
                self.add_timepoint(time_point)
        else:
            self.pd_series = None

        # Overwrite user-set parameters
        for arg in kwargs:
            setattr(self,arg,kwargs[arg])

        # Used to store the single_trial to which each analyte instance belongs
        self.parent = None  # type SingleTrial

        # Keep track of whether or not calculations need to be updated
        self.calculations_uptodate = False

        self.pd_series = None


        self.fit_params = dict()
        # self.units = {'time': 'hours',
        #               'data': 'None'}

        self._gradient = []
        # self._specific_productivity = None

        # Options
        self.removeDeathPhaseFlag = remove_death_phase_flag
        self.use_filtered_data = use_filtered_data
        self.minimum_points_for_curve_fit = minimum_points_for_curve_fit
        self.savgolFilterWindowSize = savgolFilterWindowSize

        self.death_phase_start = None
        self.blankSubtractionFlag = True

        self.stages = []
        self._stage_indices = None

        # Declare the default curve fit
        self.fit_type = 'gompertz'

    def __str__(self):
        return str(self.trial_identifier.unique_analyte_data())#'strain_name: '+str(self.trial_identifier.strain)+' media_name: '+str(self.trial_identifier.media)

    @property
    def unique_id(self):
        return ','.join([self.trial_identifier.strain,self.trial_identifier.media,self.trial_identifier.id_1,
                         self.trial_identifier.id_2, self.trial_identifier.id_3, self.trial_identifier.replicate_id])



    def serialize(self):
        serialized_dict = {'data'    : self.pd_series.to_json(), 'fit_params': self.fit_params,
                           'gradient': list(self.gradient)}
        # serialized_dict['time_vector'] = self.time_vector
        # serialized_dict['data_vector'] = self.data_vector

        try:
            serialized_dict['specific_productivity'] = list(self.specific_productivity)
        except Exception as e:
            print(e)

        serialized_dict['analyte_name'] = self.trial_identifier.analyte_name
        serialized_dict['analyte_type'] = self.trial_identifier.analyte_type

        options = {}
        for option in ['removeDeathPhaseFlag', 'use_filtered_data', 'minimum_points_for_curve_fit']:
            options[option] = getattr(self,option)
        serialized_dict['options'] = options

        return serialized_dict

    @property
    def stage_indices(self):
        return self._stage_indices

    @stage_indices.setter
    def stage_indices(self, stage_indices):
        self._stage_indices = stage_indices
        for stage_bounds in stage_indices:
            self.stages.append(self.create_stage(stage_bounds))

    @property
    def trial_identifier(self):
        return self._trial_identifier

    @trial_identifier.setter
    def trial_identifier(self, trial_identifier):
        self._trial_identifier = trial_identifier

        self.analyte_name = trial_identifier.analyte_name
        self.analyte_type = trial_identifier.analyte_type
        if self.analyte_type == 'product':
            self.fit_type = 'productionEquation_generalized_logistic'
        if self.analyte_type == 'biomass':
            self.fit_type = 'janoschek_no_limits'#'janoschek'#'gompertz'#'richard_5','growthEquation_generalized_logistic'

    @property
    def time_vector(self):
        if self.pd_series is not None:
            return np.array(self.pd_series.index)
        return None

    @time_vector.setter
    def time_vector(self, time_vector):
        if self.pd_series is None:
            self.pd_series = pd.Series(index=time_vector)
        else:
            self.pd_series.index = time_vector

        if sum(self.pd_series.index.duplicated()) > 0:
            print(self.pd_series.index)
            raise Exception('Duplicate time points found, this is not supported')

        # Fill time point list
        self.generate_time_point_list()

    @property
    def data_vector(self):
        from .settings import settings

        # Filter data to smooth noise from the signal
        if settings.use_filtered_data and len(self.pd_series)>self.savgolFilterWindowSize:
            return savgol_filter(np.array(self.pd_series), self.savgolFilterWindowSize, 3)
        else:
            return np.array(self.pd_series)

    @data_vector.setter
    def data_vector(self, data_vector):
        from .settings import settings
        live_calculations = settings.live_calculations

        # Check if an index has already been added
        if self.pd_series is None:
            self.pd_series = pd.Series(data_vector)
        else:
            self.pd_series = pd.Series(data_vector, index=self.pd_series.index)

        # Convert vectors to list format (for db)
        self.generate_time_point_list()

        # Instantiate death phase to be not detected (last point of the vector)
        self.death_phase_start = len(data_vector)

        if live_calculations:   self.calculate()

    @property
    def gradient(self):
        if self._gradient == []:
            # if self.time_vector is not None and len(self.time_vector) > 2:
            self._gradient = np.gradient(self.data_vector) / np.gradient(self.time_vector)

        return self._gradient

    def generate_time_point_list(self):
        # TODO, ensure new time point aren't created and previous ones are referenced
        self.time_points = [TimePoint(time=time, data=data)
                            for time, data in zip(self.pd_series.index, self.pd_series)]

    def calculate(self):
        from .settings import settings
        perform_curve_fit = settings.perform_curve_fit

        if self.time_vector is not None and len(self.time_vector) > 2:
            self._gradient = np.gradient(self.data_vector) / np.gradient(self.time_vector)
        if self.removeDeathPhaseFlag:
            self.find_death_phase(self.data_vector)

        if len(self.data_vector) > self.minimum_points_for_curve_fit and perform_curve_fit:
            self.curve_fit_data()

    def find_death_phase(self, data_vector):
        from .settings import settings
        use_filtered_data = settings.use_filtered_data
        verbose = settings.verbose
        self.death_phase_start = self.find_death_phase_static(data_vector,
                                                              use_filtered_data = use_filtered_data,
                                                              verbose = verbose)

    @staticmethod
    def find_death_phase_static(data_vector, use_filtered_data=False, verbose=False, hyper_parameter = 1):
        # The hyper_parameter determines the number of points
        # which need to have a negative diff to consider it death phase

        death_phase_start = len(data_vector)

        # Check if there is a reasonable difference between the min and max of the curve
        if (np.max(data_vector) - np.min(data_vector)) / np.min(data_vector) > 2:
            if verbose: print('Growth range: ', (np.max(data_vector) - np.min(data_vector)) / np.min(data_vector))

            if use_filtered_data:
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

    # def summary(self, print=False):
    #     summary = dict()
    #     summary['time_vector'] = self.time_vector
    #     summary['data_vector'] = self.data_vector
    #     summary['number_of_data_points'] = len(self.time_vector)
    #     summary['trial_identifier'] = self.trial_identifier.summary(['strain.name', 'id_1', 'id_2',
    #                                                             'analyte_name', 'titerType', 'replicate_id'])
    #     if print:
    #         print(summary)
    #
    #     return summary

    def create_stage(self, stage_bounds):
        stage = TimeCourseStage(self)#, bounds = stage_bounds)
        stage.trial_identifier = self.trial_identifier

        # Note pandas slices by index value, not index
        stage.pd_series = self.pd_series[stage_bounds[0]:stage_bounds[1]]


        # if len(self.gradient) > 0:
        #     stage.gradient = self.gradient[stage_bounds[0]:stage_bounds[1] + 1]
        # if self._specific_productivity is not None:
        #     # Set the private variable to prevent any calculations
        #     stage._specific_productivity = self._specific_productivity[stage_bounds[0]:stage_bounds[1] + 1]

        return stage

    def data_curve_fit(self, t):
        return curve_fit_dict[self.fit_type].growthEquation(np.array(t), **self.fit_params)

    @event.listens_for(TimePoint, 'load')
    def add_timepoint(self, time_point):
        from .settings import settings
        live_calculations = settings.live_calculations

        time_point.parent = self

        self.time_points.append(time_point)
        if len(self.time_points) == 1:
            self.trial_identifier = time_point.trial_identifier
            self.pd_series = pd.Series([time_point.data],index=[time_point.time])
        else:
            if self.time_points[-1].trial_identifier.unique_single_trial() \
                    != self.time_points[-2].trial_identifier.unique_single_trial():
                print(self.time_points[-1].trial_identifier)
                print(self.time_points[-2].trial_identifier)

                raise Exception("Attempted to add time point with non-matching identifier")

            # Check if ordering is broken
            if self.time_points[-1].time < self.time_points[-2].time:
                self.time_points.sort(key=lambda timePoint: timePoint.time)
                self.pd_series = pd.Series([timePoint.data for timePoint in self.time_points],
                                           index=[timePoint.time for timePoint in self.time_points])
            else:
                # Otherwise simply append
                self.pd_series = self.pd_series.append(pd.Series([time_point.data],index=[time_point.time]))

        if sum(self.pd_series.index.duplicated()) > 0:
            print(self.pd_series)
            print(self.trial_identifier)
            print(time_point.trial_identifier)
            raise Exception('Duplicate time points found, this is not supported')

        if len(self.time_points) > 6 and live_calculations:
            self.gradient = np.gradient(self.data_vector) / np.gradient(self.time_vector)

    def curve_fit_data(self):
        from .settings import settings
        verbose = settings.verbose

        if self.trial_identifier.analyte_type == 'titer' or self.trial_identifier.analyte_type in ['substrate', 'product']:
            print(
                'Curve fitting for titers unimplemented in restructured curve fitting. Please see Depricated\depicratedCurveFittingCode.py')

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



            if verbose:
                print('Started fit')
                print('Death phase start: ', self.death_phase_start)

            result = curve_fit_dict[self.fit_type].calcFit(self.time_vector[0:self.death_phase_start],
                                                           self.data_vector[0:self.death_phase_start])
            #,fit_kws = {'xatol':1E-10, 'fatol':1E-10})  # , fit_kws = {'maxfev': 20000, 'xtol': 1E-12, 'ftol': 1E-12})
            if verbose: print('Finished fit')

            for key in result.best_values:
                temp_param = FitParameter(key, result.best_values[key])
                self.fit_params[key] = temp_param # result.best_values[key]

            if verbose:
                import matplotlib.pyplot as plt
                plt.figure()
                plt.plot(self.time_vector[0:self.death_phase_start], self.data_vector[0:self.death_phase_start], 'bo')
                plt.plot(self.time_vector[0:self.death_phase_start], result.best_fit, 'r-')

            if verbose: print(result.fit_report())
        else:
            print('Unidentified titer type:' + self.trial_identifier.analyte_type)
            print('Ensure that the trial identifier is described before adding data. This will allow curve fitting'
                  'to be appropriate to the analyte type.')

class TimeCourseStage(TimeCourse):
    stage_parent_id = Column(Integer, ForeignKey('time_course.id'))
    parent = relationship('TimeCourse',uselist=False)

    def __init__(self, parent):
        self.parent = parent
        super(TimeCourseStage, self).__init__()


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

    def add_timepoint(self, time_point):
        if len(self.time_points) < 2:
            self.time_points.append(time_point)
        else:
            raise Exception("Cannot have more than two timePoints for an endPoint Object")

        if len(self.time_points) == 2:
            self.time_points.sort(key=lambda timePoint: timePoint.time)

# class AnalyteFeature(object):
