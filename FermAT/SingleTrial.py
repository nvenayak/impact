import numpy as np
import dill as pickle

import sqlite3 as sql

from FermAT.TrialIdentifier import RunIdentifier

class SingleTrial(object):
    """
    Container for single experiment data. This includes all data for a single strain (OD, titers, fluorescence, etc.)
    """

    def __init__(self):
        self._t = np.array([])
        self.titerObjectDict = dict()
        self.runIdentifier = RunIdentifier()
        self.yields = dict()

        self.substrate_name = None
        self.product_names = []
        self.biomass_name = None

    # Setters and Getters
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

    def commitToDB(self, replicateID, c=None, stat=None):
        if stat is None:
            stat_prefix = ''
        else:
            stat_prefix = '_' + stat

        c.execute(
            """INSERT INTO singleTrialTable""" + stat_prefix + """(replicateID, replicate, yieldsDict) VALUES (?, ?, ?)""",
            (replicateID, self.runIdentifier.replicate, pickle.dumps(self.yields)))

        c.execute("""SELECT MAX(singleTrialID""" + stat_prefix + """) from singleTrialTable""" + stat_prefix + """""")
        singleTrialID = c.fetchall()[0][0]

        for key in self.titerObjectDict:
            self.titerObjectDict[key].commitToDB(singleTrialID, c=c, stat=stat)

    def loadFromDB(self, singleTrialID=None, c=None, stat=None):
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

        c.execute("""SELECT timeCourseID, singleTrial""" + stat_prefix + """ID, titerType, titerName, timeVec, dataVec, rate FROM
                timeCourseTable""" + stat_prefix + """ WHERE singleTrial""" + stat_prefix + """ID == ? """,
                  (singleTrialID,))
        for row in c.fetchall():
            product = row[3]
            self.titerObjectDict[product] = TimeCourse()
            self.titerObjectDict[product].runIdentifier.titerType = row[2]
            self.titerObjectDict[product].runIdentifier.titerName = row[3]
            if stat_prefix == '':
                self.titerObjectDict[product]._timeVec = np.loads(row[4])
            self.titerObjectDict[product]._dataVec = np.loads(row[5])
            self.titerObjectDict[product].rate = pickle.loads(row[6])

            self._t = self.titerObjectDict[product].timeVec

    def calculate_specific_productivity(self):
        if self.biomass_name is None:
            return 'Biomass not defined'

        for product in self.product_names + [self.biomass_name]:
            self.titerObjectDict[product].specific_productivity = self.titerObjectDict[product].gradient / \
                                                                  self.titerObjectDict[self.biomass_name].dataVec

    def calculate_ODE_fit(self):
        biomass = self.titerObjectDict[self.biomass_name].dataVec
        biomass_rate = np.gradient(self.titerObjectDict[self.biomass_name].dataVec) / np.gradient(
            self.titerObjectDict[self.biomass_name].timeVec)
        self.titerObjectDict[self.substrate_name]
        self.titerObjectDict[self.product_names]

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

    def calcMassBalance(self, OD_gdw=None, calculateFBACO2=False):
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
        #     # substrate.lower_bound = self.substrate.dataVec[-1]
        #     # substrate.upper_bound = self.substrate.dataVec[-1]
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
            biomass_gdw = self._OD.dataVec / OD_gdw
        else:
            biomass_gdw = None

        # Calculate the mass of products consumed
        totalProductMass = np.sum([self.products[productKey].dataVec for productKey in self.products], axis=0)

        # Calculate the mass balance (input-output)
        if biomass_gdw is None:   biomass_gdw = np.zeros(
            [len(self.substrateConsumed)])  # If this isn't defined, set biomass to zero
        massBalance = self.substrateConsumed - totalProductMass - biomass_gdw

        return {'substrateConsumed': self.substrateConsumed,
                'totalProductMass' : totalProductMass,
                'biomass_gdw'      : biomass_gdw,
                'massBalance'      : massBalance}

    def addTiterObject(self, titerObject):
        # Check if this titer already exists
        if titerObject.runIdentifier.titerName in self.titerObjectDict:
            raise Exception('A duplicate titer was added to the singleTiterObject: ',
                            titerObject.runIdentifier.titerName)

        self.titerObjectDict[titerObject.runIdentifier.titerName] = titerObject

        if titerObject.runIdentifier.titerType == 'substrate':
            if self.substrate_name is None:
                self.substrate_name = titerObject.runIdentifier.titerName
            else:
                raise Exception('No support for Multiple substrates: ', self.substrate_name, ' ',
                                titerObject.runIdentifier.titerName)
            self.calcSubstrateConsumed()

        if titerObject.runIdentifier.titerType == 'biomass' or titerObject.runIdentifier.titerType == 'OD':
            if self.biomass_name is None:
                self.biomass_name = titerObject.runIdentifier.titerName
            else:
                raise Exception('No support for Multiple biomasses: ', self.biomass_name, ' ',
                                titerObject.runIdentifier.titerName)

        if titerObject.runIdentifier.titerType == 'product':
            self.product_names.append(titerObject.runIdentifier.titerName)

        if 'substrate' in [self.titerObjectDict[key].runIdentifier.titerType for key in self.titerObjectDict] and \
                        'product' in [self.titerObjectDict[key].runIdentifier.titerType for key in
                                      self.titerObjectDict]:
            self.calcYield()

        self.checkTimeVectors()
        self.runIdentifier = titerObject.runIdentifier
        self.runIdentifier.time = None

    def checkTimeVectors(self):
        checkTimeVectorsFlag = 1
        if checkTimeVectorsFlag == 1:
            t = []
            flag = 0

            # print(len(self.titerObjectDict))
            for key in self.titerObjectDict:
                # print(self.titerObjectDict[key].timeVec)
                # print(self.titerObjectDict[key].timeVec)
                t.append(self.titerObjectDict[key].timeVec)
            # print(t)
            # print('--------')
            for i in range(len(t) - 1):
                if (t[i] != t[i + 1]).all():
                    index = i
                    flag = 1
            # print(t)
            # print(t.count(t[0]))
            # print(len(t))
            # if t.count(t[0]) != len(t):
            #     flag = 1

            if flag == 1:
                # print(t[index])
                # print(t[index+1])
                raise (Exception(
                    "Time vectors within an experiment don't match, must implement new methods to deal with this type of data (if even possible)"))
            else:
                self._t = t[0]

    def getUniqueTimePointID(self):
        return self.substrate.runIdentifier.strainID + self.substrate.runIdentifier.identifier1 + self.substrate.runIdentifier.identifier2 + str(
            self.substrate.runIdentifier.replicate)

    def getUniqueReplicateID(self):
        return self.titerObjectDict[list(self.titerObjectDict.keys())[0]].getReplicateID()

    def calcSubstrateConsumed(self):
        self.substrateConsumed = np.array(
            [(self.titerObjectDict[self.substrate_name].dataVec[0] - dataPoint) for dataPoint in
             self.titerObjectDict[self.substrate_name].dataVec])

    def calcYield(self):
        self.yields = dict()
        for productKey in [key for key in self.titerObjectDict if
                           self.titerObjectDict[key].runIdentifier.titerType == 'product']:
            self.yields[productKey] = np.divide(self.titerObjectDict[productKey].dataVec, self.substrateConsumed)


class SingleTrialDataShell(SingleTrial):
    """
    Object which overwrites the SingleTrial objects setters and getters, acts as a shell of data with the
    same structure as SingleTrial
    """

    def __init__(self):
        SingleTrial.__init__(self)

    @SingleTrial.substrate.setter
    def substrate(self, substrate):
        self._substrate = substrate

    @SingleTrial.OD.setter
    def OD(self, OD):
        self._OD = OD

    @SingleTrial.products.setter
    def products(self, products):
        self._products = products