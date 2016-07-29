class RunIdentifier(object):
    """
    Carries information about the run through all the objects

    Attributes
    -----------
    strainID : str
        Strain name e.g. 'MG1655 del(adh,pta)'
    identifier1 : str, optional
        First identifier, plasmid e.g. 'pTrc99a'
    identifier2 : str, optional
        Second identifier, inducer e.g. 'IPTG'
    replicate : str
        The replicate number, e.g. '1','2','3','4'
    time : float
        The time of the data point, only relevant in :class:`~TimePoint` objects
    titerName : str
        The name of the titer, e.g. 'OD600','Lactate','Ethanol','Glucose'
    titerType : str
        The type of titer, three acceptable values e.g. 'biomass','substrate','product'
    """

    def __init__(self):
        self.strainID = ''  # e.g. MG1655 dlacI
        self.identifier1 = ''  # e.g. pTOG009
        self.identifier2 = ''  # e.g. IPTG
        self.replicate = None  # e.g. 1
        self.time = -1  # e.g. 0
        self.titerName = 'None'  # e.g. Lactate
        self._titerType = 'None'  # e.g. titer or OD

    @property
    def titerType(self):
        return self._titerType

    @titerType.setter
    def titerType(self, titerType):
        if titerType in ['biomass', 'OD', 'OD600']:
            self._titerType = 'biomass'
            if titerType in ['OD', 'OD600']:
                print('Please use biomass titerType instead of: ', titerType)
        elif titerType in ['product', 'substrate']:
            self._titerType = titerType
        else:
            raise Exception('Titer type is not supported: ', titerType)

    def summary(self, items):
        summary = dict()
        for item in items:
            summary[item] = getattr(self,item)
        return summary

    def parse_RunIdentifier_from_csv(self, csv_RunIdentifier):
        """
        Used to parse a CSV runIdentifier

        Parameters
        ----------
        csv_RunIdentifier : str 
            a comma-separated string containing a RunIdentifier in standard form - strainID,identifier1,identifier2,replicate
        """
        if type(csv_RunIdentifier) is str:
            tempParsedIdentifier = csv_RunIdentifier.split(',')
            if len(tempParsedIdentifier) == 0:
                print(tempParsedIdentifier, " <-- not processed")
            if len(tempParsedIdentifier) > 0:
                self.strainID = tempParsedIdentifier[0]
            if len(tempParsedIdentifier) > 1:
                self.identifier1 = tempParsedIdentifier[1]
            if len(tempParsedIdentifier) > 2:
                self.identifier2 = tempParsedIdentifier[2]
            if len(tempParsedIdentifier) > 3:
                try:
                    self.replicate = int(tempParsedIdentifier[3])
                except:
                    print("Couldn't parse replicate from ", tempParsedIdentifier)
            if len(tempParsedIdentifier) > 4:
                self.time = float(tempParsedIdentifier[4])

    def get_unique_for_SingleTrial(self):
        return self.strainID + self.identifier1 + self.identifier1 + str(
            self.replicate) + self.titerName + self.titerType

    def get_unique_id_for_ReplicateTrial(self):
        """
        Get the unique information for a single replicate
        Returns
        -------
        unique_id : str
            Unique id defining a replicate.
        """
        return self.strainID + self.identifier1 + self.identifier2

        # def return_unique_experiment_id(self):
        #     return self.strainID + self.identifier1 + self.identifier2 + str(self.replicate)