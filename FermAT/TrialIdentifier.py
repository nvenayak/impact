class TrialIdentifier(object):
    """
    Carries information about the run through all the objects

    Attributes
    -----------
    strain_id : str
        Strain name e.g. 'MG1655 del(adh,pta)'
    id_1 : str, optional
        First identifier, plasmid e.g. 'pTrc99a'
    id_2 : str, optional
        Second identifier, inducer e.g. 'IPTG'
    replicate_id : str
        The replicate number, e.g. '1','2','3','4'
    time : float
        The time of the data point, only relevant in :class:`~TimePoint` objects
    analyte_name : str
        The name of the titer, e.g. 'OD600','Lactate','Ethanol','Glucose'
    titerType : str
        The type of titer, three acceptable values e.g. 'biomass','substrate','product'
    """

    def __init__(self, strain_id='', id_1='', id_2='', id_3='',
                 replicate_id = None, time = -1, analyte_name = 'None',
                 analyte_type = 'None'):
        self.strain_id = strain_id          # e.g. MG1655 dlacI
        self.id_1 = id_1                    # e.g. pTOG009
        self.id_2 = id_2                    # e.g. IPTG
        self.id_3 = id_3                    # e.g. 37C
        self.replicate_id = replicate_id    # e.g. 1
        self.time = time                    # e.g. 0
        self.analyte_name = analyte_name    # e.g. Lactate
        self._analyte_type = analyte_type   # e.g. titer or OD

    @property
    def analyte_type(self):
        return self._analyte_type

    @analyte_type.setter
    def analyte_type(self, titerType):
        if titerType in ['biomass', 'OD', 'OD600']:
            self._analyte_type = 'biomass'
            if titerType in ['OD', 'OD600']:
                print('Please use biomass titerType instead of: ', titerType)
        elif titerType in ['product', 'substrate']:
            self._analyte_type = titerType
        else:
            raise Exception('AnalyteData type is not supported: ', titerType)

    def summary(self, items):
        summary = dict()
        for item in items:
            summary[item] = getattr(self, item)
        return summary

    def parse_trial_identifier_from_csv(self, csv_trial_identifier):
        """
        Used to parse a CSV trial_identifier

        Parameters
        ----------
        csv_trial_identifier : str
            a comma-separated string containing a TrialIdentifier in standard form - strain_id,id_1,id_2,replicate_id
        """
        if type(csv_trial_identifier) is str:
            tempParsedIdentifier = csv_trial_identifier.split(',')
            if len(tempParsedIdentifier) == 0:
                print(tempParsedIdentifier, " <-- not processed")
            if len(tempParsedIdentifier) > 0:
                self.strain_id = tempParsedIdentifier[0]
            if len(tempParsedIdentifier) > 1:
                self.id_1 = tempParsedIdentifier[1]
            if len(tempParsedIdentifier) > 2:
                self.id_2 = tempParsedIdentifier[2]
            if len(tempParsedIdentifier) > 3:
                try:
                    self.replicate_id = int(tempParsedIdentifier[3])
                except:
                    print("Couldn't parse replicate_id from ", tempParsedIdentifier)
            if len(tempParsedIdentifier) > 4:
                self.time = float(tempParsedIdentifier[4])

    def get_unique_for_SingleTrial(self):
        return self.strain_id + self.id_1 + self.id_1 + str(
            self.replicate_id) + self.analyte_name + self.analyte_type

    def get_unique_id_for_ReplicateTrial(self):
        """
        Get the unique information for a single replicate_id
        Returns
        -------
        unique_id : str
            Unique id defining a replicate_id.
        """
        return self.strain_id + self.id_1 + self.id_2

        # def return_unique_experiment_id(self):
        #     return self.strain_id + self.id_1 + self.id_2 + str(self.replicate_id)
