import numpy as np
import dill as pickle
import pandas as pd
import sqlite3 as sql
import warnings

from .TrialIdentifier import TrialIdentifier
from .AnalyteData import TimeCourse

from django.db import models
from ..database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, PickleType, Float
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection

class Yield(object):
    pass

class SingleTrial(Base):
    """
    Container for :class:`~TiterObject` to build a whole trial out of different measurements. E.g. one flask would
    contain data for biomass (OD), products (ethanol, acetate), substrates (glucose), fluorescence (gfpmut3, mCherry)
    """

    __tablename__ = 'single_trial'

    id = Column(Integer, primary_key=True)

    trial_identifier_id = Column(Integer,ForeignKey('trial_identifier.id'))
    _trial_identifier = relationship('TrialIdentifier')

    analyte_dict = relationship('TimeCourse',
                                collection_class = attribute_mapped_collection('keyword'),
                                cascade = 'save-update, delete')

    analyte_df = Column(PickleType)
    yields = Column(PickleType)
    yields_df = Column(PickleType)

    _substrate_name = Column(PickleType)
    product_names = Column(PickleType)
    biomass_name = Column(PickleType)

    stage_indices = Column(PickleType)

    parent_id = Column(Integer, ForeignKey('replicate_trial.id'))

    stage_parent_id = Column(Integer, ForeignKey('single_trial.id'))
    stages = relationship('SingleTrial', foreign_keys = 'SingleTrial.stage_parent_id')

    normalized_data = Column(PickleType)



    def __init__(self):
        # Trial identifier with relevant features common to the trial
        self._trial_identifier = None

        # Analyte objects
        self.analyte_dict = dict()

        # Dataframe containing all of the analytes with a common index
        self.analyte_df = pd.DataFrame()

        # Dict and df containing yields for each product
        self.yields = dict()
        self.yields_df = pd.DataFrame()

        # Contains the names of different analyte types
        self._substrate_name = None
        self.product_names = []
        self.biomass_name = None

        # Contains information about the stages used in the experiment, TODO
        self.stage_indices = None
        self.stage_list = None

        # Data normalized to different features, not serialized
        self.normalized_data = dict()

    def serialize(self):
        serialized_dict = {}

        if self.trial_identifier:
            serialized_dict['strain_id'] = self.trial_identifier.strain_id
            serialized_dict['id_1'] = self.trial_identifier.id_1
            serialized_dict['id_2'] = self.trial_identifier.id_2

        for analyte_name in self.analyte_dict:
            serialized_dict[analyte_name] = self.analyte_dict[analyte_name].serialize()

        serialized_dict['yields'] = self.yields_df.to_json()

        return serialized_dict

    # Setters and Getters
    @property
    def stages(self):
        return self._stages

    @stages.setter
    def stages(self, stages):
        """
        Creates stages when they are defined

        Parameters
        ----------
        stages : list of stage start and end lists [start_index, end_index]

        """
        self._stages = stages

        for stage in stages:
            stage = self.create_stage(stage)
            self.stage_list.append(stage)

    @property
    def substrate_name(self):
        return self._substrate_name

    @substrate_name.setter
    def substrate_name(self, substrate_name):
        self._substrate_name = substrate_name
        # self.check_time_vectors_match()
        self.calculate_substrate_consumed()
        if len(self.product_names) > 0:
            self.calculate_yield()

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
            self.calculate_yield()

    @property
    def trial_identifier(self):
        return self._trial_identifier

    @trial_identifier.setter
    def trial_identifier(self, trial_identifier):
        self._trial_identifier = trial_identifier

    def calculate(self):
        for analyte_key in self.analyte_dict:
            self.analyte_dict[analyte_key].calculate()

    def normalize_data(self, normalize_to):
        for product in self.product_names:
            self.normalized_data[product] = self.analyte_dict[product] / self.analyte_dict[normalize_to]

    def create_stage(self, stage_bounds):
        stage = SingleTrial()
        for titer in self.analyte_dict:
            stage.add_titer(self.analyte_dict[titer].create_stage(stage_bounds))
        stage.calculate_yield()

        return stage

    def db_commit(self, replicateID, c=None, stat=None):
        """
        Commit object to database.

        Parameters
        ----------
        replicateID : int
            replicateID to commit to
        c : sql cursor
        stat : str
            If this is a statistic (avg, std), which statistic? None is used for raw data.
        """
        if stat is None:
            stat_prefix = ''
        else:
            # Trial identifier not required for storing replicates, here's a temp one
            self.trial_identifier = TrialIdentifier()
            stat_prefix = '_' + stat

        c.execute(
            """INSERT INTO singleTrialTable""" + stat_prefix + """(replicateID, replicate_id, yieldsDict) VALUES (?, ?, ?)""",
            (replicateID, self.trial_identifier.replicate_id, pickle.dumps(self.yields)))

        c.execute("""SELECT MAX(singleTrialID""" + stat_prefix + """) from singleTrialTable""" + stat_prefix + """""")
        singleTrialID = c.fetchall()[0][0]

        for key in self.analyte_dict:
            self.analyte_dict[key].db_commit(singleTrialID, c=c, stat=stat)

    def db_load(self, singleTrialID=None, c=None, stat=None):
        """
        Load object from database.

        Parameters
        ----------
        singleTrialID : int
            The singleTrialID to load
        c : SQL cursor
        stat : str
            If this is a statistic (avg, std), which statistic? None is used for raw data.

        Returns
        -------

        """
        c.execute("""SELECT yieldsDict FROM singleTrialTable WHERE singleTrialID == ?""", (singleTrialID,))
        data = c.fetchall()[0][0]
        self.yields = pickle.loads(data)

        if stat is None:
            stat_prefix = ''
        else:
            stat_prefix = '_' + stat

        c.execute(
            """SELECT yieldsDict FROM singleTrialTable""" + stat_prefix + """ WHERE singleTrialID""" + stat_prefix + """ == ?""",
            (singleTrialID,))
        temp = c.fetchall()

        data = temp[0][0]

        self.yields = pickle.loads(data)

        c.execute("""SELECT timeCourseID, singleTrial""" + stat_prefix + """ID, titerType, analyte_name, time_vector, data_vector, fit_params FROM
                timeCourseTable""" + stat_prefix + """ WHERE singleTrial""" + stat_prefix + """ID == ? """,
                  (singleTrialID,))
        for row in c.fetchall():
            # product = row[3]
            temp_titer_object = TimeCourse()
            for attribute in ['strain_id', 'id_1', 'id_2']:
                setattr(temp_titer_object.trial_identifier, attribute, getattr(self.trial_identifier, attribute))
            temp_titer_object.trial_identifier.id_1 = self.trial_identifier.id_1
            temp_titer_object.trial_identifier.id_2 = self.trial_identifier.id_2
            temp_titer_object.trial_identifier.analyte_type = row[2]
            temp_titer_object.trial_identifier.analyte_name = row[3]

            if stat_prefix == '':
                temp_titer_object.trial_identifier.replicate_id = self.trial_identifier.replicate_id
                temp_titer_object._time_vector = np.loads(row[4])
                temp_titer_object.pd_series = pd.Series(np.loads(row[5]), index=np.loads(row[4]))
                # print(temp_titer_object._time_vector)
            else:
                temp_titer_object.pd_series = pd.Series(np.loads(row[5]))
            temp_titer_object._data_vector = np.loads(row[5])
            # try:
            #     temp_titer_object.pd_series = pd.Series(np.loads(row[5]), index=np.loads(row[4]))
            # except Exception as e:
            #     print(np.loads(row[5]))
            #     print(np.loads(row[4]))
            #     raise Exception(e)
            temp_titer_object.fit_params = pickle.loads(row[6])

            # self._t = self.titer_dict[product].time_vector

            self.add_titer(temp_titer_object)


        # The yields get recalculated when the titers are added, when in reality. A quick solution is to set the yield
        # to the correct values after adding all the titer objects (the std of the yield is not the ratio of the stds)
        self.yields = pickle.loads(data)

    def summary(self, print=False):
        summary = dict()
        summary['substrate'] = self._substrate_name
        summary['products'] = self.product_names
        summary['biomass'] = self.biomass_name
        summary['number_of_data_points'] = len(self._t)
        summary['run_identifier'] = self.trial_identifier.summary(['strain_id', 'id_1', 'id_2',
                                                                'replicate_id'])

        if print:
            print(summary)

        return summary

    def calculate_specific_productivity(self):
        """
        Calculate the specific productivity (dP/dt) given :math:`dP/dt = k_{Product} * X`
        """
        if self.biomass_name is None:
            return 'Biomass not defined'

        for product in self.product_names + [self.biomass_name] + [self.substrate_name]:
            self.analyte_dict[product].specific_productivity = self.analyte_dict[product].gradient / \
                                                               self.analyte_dict[self.biomass_name].data_vector

    def calculate_ODE_fit(self):
        """
        WIP to fit the data to ODEs
        """
        biomass = self.analyte_dict[self.biomass_name].data_vector
        biomass_rate = np.gradient(self.analyte_dict[self.biomass_name].data_vector) / np.gradient(
            self.analyte_dict[self.biomass_name].time_vector)
        self.analyte_dict[self.substrate_name]
        self.analyte_dict[self.product_names]

        def dFBA_functions(y, t, rate):
            # Append biomass, substrate and products in one list
            exchange_reactions = biomass_flux + substrate_flux + product_flux
            # y[0]           y[1]
            dydt = []
            for exchange_reaction in exchange_reactions:
                if y[1] > 0:  # If there is substrate
                    dydt.append(exchange_reaction * y[0])
                else:  # If there is not substrate
                    dydt.append(0)
            return dydt

        import numpy as np
        from scipy.integrate import odeint

        # Let's assign the data to these variables
        biomass_flux = []
        biomass_flux.append(model.solution.x_dict[biomass_keys[0]])

        substrate_flux = []
        substrate_flux.append(model.solution.x_dict[substrate_keys[0]])

        product_flux = [model.solution.x_dict[key] for key in product_keys]

        exchange_keys = biomass_keys + substrate_keys + product_keys

        # Now, let's build our model for the dFBA
        def dFBA_functions(y, t, biomass_flux, substrate_flux, product_flux):
            # Append biomass, substrate and products in one list
            exchange_reactions = biomass_flux + substrate_flux + product_flux
            # y[0]           y[1]
            dydt = []
            for exchange_reaction in exchange_reactions:
                if y[1] > 0:  # If there is substrate
                    dydt.append(exchange_reaction * y[0])
                else:  # If there is not substrate
                    dydt.append(0)
            return dydt

        # Now let's generate the data
        sol = odeint(dFBA_functions, y0, t,
                     args=([flux * np.random.uniform(1 - noise, 1 + noise) for flux in biomass_flux],
                           [flux * np.random.uniform(1 - noise, 1 + noise) for flux in
                            substrate_flux],
                           [flux * np.random.uniform(1 - noise, 1 + noise) for flux in
                            product_flux]))

        dFBA_profile = {key: [row[i] for row in sol] for i, key in enumerate(exchange_keys)}

    def calculate_mass_balance(self, OD_gdw=None, calculateFBACO2=False):
        """
        Calculate a mass balance given the supplied substrate and products

        Parameters
        ----------
        OD_gdw : float
            The correlation betwen OD_gdw and OD600
        calculateFBACO2 : bool
            Flag to calculate the CO2 using FBA (not implemented yet)
        """
        # if calculateFBACO2:
        #     import cobra
        #
        #     # Load the COBRA model
        #     ...
        #
        #     # Convert the common names to COBRA model names
        #     commonNameCobraDictionary = {'Lactate'  : ...,
        #                                  'Ethanol'  : ...,
        #                                  'Acetate'  : ...,
        #                                  'Formate'  : ...,
        #                                  'Glycolate': ...,
        #                                  'Glucose'  : ...,
        #                                  'Succinate': ...
        #                                  }
        #
        #     # Get the molar mass from COBRA model and covert the grams to mmol
        #     substrate = model.metabolites.get_by_id(substrate_name)
        #     # substrate_mmol = substrate.formulaWeight()
        #     # substrate.lower_bound = self.substrate.data_vector[-1]
        #     # substrate.upper_bound = self.substrate.data_vector[-1]
        #     productsCOBRA = dict()
        #     for key in self.yields:
        #         modelMetID = commonNameCobraDictionary[key]
        #         productsCOBRA[key] = model.metabolites.get_by_id(modelMetID)
        #
        #     # Set the bounds
        #     ...
        #
        #     # Run the FBA and return the CO2
        #     ...

        if type(OD_gdw) == None:
            # Parameters for E. coli
            OD_gdw = 0.33  # Correlation for OD to gdw for mass balance

        # self.substrateConsumed

        if self.OD is not None:
            # Calc mass of biomass
            biomass_gdw = self._OD.data_vector / OD_gdw
        else:
            biomass_gdw = None

        # Calculate the mass of products consumed
        totalProductMass = np.sum([self.products[productKey].data_vector for productKey in self.products], axis=0)

        # Calculate the mass balance (input-output)
        if biomass_gdw is None:   biomass_gdw = np.zeros(
            [len(self.substrateConsumed)])  # If this isn't defined, set biomass to zero
        massBalance = self.substrateConsumed - totalProductMass - biomass_gdw

        return {'substrateConsumed': self.substrateConsumed,
                'totalProductMass' : totalProductMass,
                'biomass_gdw'      : biomass_gdw,
                'massBalance'      : massBalance}

    def add_titer(self, titerObject):
        """
        Add a :class:`~TiterObject`

        Parameters
        ----------
        titerObject : :class:`~TiterObject`
            A titer object to be added

        """
        from .settings import settings
        live_calculations = settings.live_calculations

        # Check if this titer already exists
        if titerObject.trial_identifier.analyte_name in self.analyte_dict:
            raise Exception('A duplicate titer was added to the singleTiterObject,\n'
                            'Make sure replicates are defined properly,\n'
                            'Duplicate TrialIdentifier: ',
                            vars(titerObject.trial_identifier))

        # Set the parent
        titerObject.parent = self

        self.analyte_dict[titerObject.trial_identifier.analyte_name] = titerObject

        if titerObject.trial_identifier.analyte_type == 'substrate':
            if self.substrate_name is None:
                self.substrate_name = titerObject.trial_identifier.analyte_name
            else:
                raise Exception('No support for Multiple substrates: ', self.substrate_name, ' ',
                                titerObject.trial_identifier.analyte_name)
            self.calculate_substrate_consumed()

        if titerObject.trial_identifier.analyte_type in ['biomass','OD']:
            if self.biomass_name is None:
                self.biomass_name = titerObject.trial_identifier.analyte_name
            else:
                raise Exception('No support for Multiple biomasses: ', self.biomass_name, ' ',
                                titerObject.trial_identifier.analyte_name)

        if titerObject.trial_identifier.analyte_type == 'product':
            self.product_names.append(titerObject.trial_identifier.analyte_name)

            if self.substrate_name is not None:
                self.calculate_yield()

        # self.check_time_vectors_match()

        # check if trial identifiers match
        if self.trial_identifier is None:
            self.trial_identifier = TrialIdentifier()
            for attr in ['strain_id', 'id_1', 'id_2', 'replicate_id']:
                setattr(self.trial_identifier, attr, getattr(titerObject.trial_identifier, attr))

        for attr in ['strain_id','id_1','id_2','replicate_id']:
            if getattr(self.trial_identifier,attr) != getattr(titerObject.trial_identifier,attr):
                raise Exception('Trial identifiers do not match at the following attribute: '
                                +attr
                                +' val 1: '
                                +getattr(self.trial_identifier,attr)
                                +' val 2: '
                                +getattr(titerObject.trial_identifier,attr))
            else:
                setattr(self.trial_identifier, attr, getattr(titerObject.trial_identifier, attr))


        self.trial_identifier.time = None

        # Pandas support
        temp_analyte_df = pd.DataFrame()
        temp_analyte_df[titerObject.trial_identifier.analyte_name] = titerObject.pd_series

        # Merging the dataframes this way will allow different time indices for different analytes
        # print(self.analyte_df)
        # print(temp_analyte_df)
        self.analyte_df = pd.merge(self.analyte_df,temp_analyte_df,left_index=True,right_index=True, how='outer')
        self.t = self.analyte_df.index

    # def check_time_vectors_match(self):
    #     """
    #     Ensure that the time vectors match between :class:`~AnalyteData` objects. Functionality to deal with missing data or
    #     data with different sizes is not implemented.
    #     """
    #     checkTimeVectorsFlag = 1
    #     if checkTimeVectorsFlag == 1:
    #         t = []
    #         flag = 0
    #
    #         for key in self.analyte_dict:
    #             # print(self.analyte_dict[key].time_vector)
    #             t.append(self.analyte_dict[key]._time_vector)
    #
    #             # print(t)
    #         for i in range(len(t) - 1):
    #             if (t[i] != t[i + 1]).all():
    #                 index = i
    #                 flag = 1
    #
    #         if flag == 1:
    #             warnings.warn("Deprecated. New pandas functinality will enable analysis with differently sized data", DeprecationWarning)
    #         else:
    #             self._t = t[0]

    def get_unique_timepoint_id(self):
        return self.substrate.trial_identifier.strain_id + self.substrate.trial_identifier.id_1 + self.substrate.trial_identifier.id_2 + str(
            self.substrate.trial_identifier.replicate_id)

    def get_unique_replicate_id(self):
        return self.analyte_dict[list(self.analyte_dict.keys())[0]].getReplicateID()

    def get_time(self, stage=None):
        if stage is not None:
            return self.t[self.stages[stage][0]:self.stages[stage][1]]
        else:
            return self.t

    def get_yields(self):
            return self.yields

    def calculate_substrate_consumed(self):
        self.substrateConsumed = np.array(
            [(self.analyte_dict[self.substrate_name].data_vector[0] - dataPoint) for dataPoint in
             self.analyte_dict[self.substrate_name].data_vector])

    def calculate_yield(self):
        self.yields = dict()
        for productKey in [key for key in self.analyte_dict if
                           self.analyte_dict[key].trial_identifier.analyte_type == 'product']:
            try:
                self.yields[productKey] = np.divide(
                    [(dataPoint - self.analyte_dict[productKey].data_vector[0]) for dataPoint in
                     self.analyte_dict[productKey].data_vector],
                    self.substrateConsumed)
            except Exception as e:
                print(productKey)
                print(self.analyte_dict[productKey].data_vector)
                print(e)


# class TimeCourseStage(TimeCourse):
#     def __init__(self):
#         TimeCourse().__init__()
        #
        # @TimeCourse.stage_indices.setter
        # def

        # class SingleTrialDataShell(SingleTrial):
        #     """
        #     Object which overwrites the SingleTrial objects setters and getters, acts as a shell of data with the
        #     same structure as SingleTrial
        #     """
        #
        #     def __init__(self):
        #         SingleTrial.__init__(self)
        #
        #     @SingleTrial.substrate.setter
        #     def substrate(self, substrate):
        #         self._substrate = substrate
        #
        #     @SingleTrial.OD.setter
        #     def OD(self, OD):
        #         self._OD = OD
        #
        #     @SingleTrial.products.setter
        #     def products(self, products):
        #         self._products = products
