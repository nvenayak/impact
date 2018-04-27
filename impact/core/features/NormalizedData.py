from .Base import *

class ODNormalizedData(BaseAnalyteFeature):
    # The constructor should accept all required analytes as parameters
    def __init__(self, biomass, reporter):
        self.biomass = biomass
        self.reporter = reporter
        self.normalized_data = None

    # This data property assures that the data is returned, or calculated as needed
    @property
    def data(self):
        if self.normalized_data is None:
            self.calculate()
        return self.normalized_data

    # This is where the property is actually calculated and set
    def calculate(self):
        self.normalized_data = self.reporter.data_vector / self.biomass.data_vector


# The feature factory watches for those analytes
class ODNormalizedDataFactory(BaseAnalyteFeatureFactory):
    # define what the feature
    requires = ['biomass', 'reporter']
    name = 'od_normalized_data'

    # constructor should initialize variables until all required analytes are present,
    # this will ensure that despite the order analytes are added, feature will be calculated appropriately
    def __init__(self):
        self.biomass = None
        self.reporter = None

    # define how to handle new analytes
    def add_analyte_data(self, analyte_data):
        if analyte_data.trial_identifier.analyte_type == 'reporter':
            self.reporter = analyte_data
        elif analyte_data.trial_identifier.analyte_type == 'biomass':
            self.biomass = analyte_data

        if self.reporter is not None and self.biomass is not None:
            setattr(analyte_data, self.name, ODNormalizedData(self.biomass, self.reporter))


class NormalizedData(BaseAnalyteFeature):
    """
    Normalizes a given analyte to another
    """
    def __init__(self, analyte, normalization_analyte):
        self.analyte = analyte
        self.normalization_analyte = normalization_analyte

    @property
    def data(self):
        return self.analyte / self.normalization_analyte


class NormalizedDataFactory(BaseAnalyteFeatureFactory):
    requires = ['product','substrate','biomass']
    name = 'normalized_data'

    def __init__(self):
        """
        Initialize any required variables here.
        """
        self.analytes = []
        raise Exception('Must be implemented in child')

    def add_analyte_data(self, analyte):
        """
        Function called when new analyte is added. If an analyte is required for this feature, ensure to save or
        use analyte. Do not manipulate raw analyte data.
        Parameters
        ----------
        analyte_data

        Returns
        -------

        """
        self.analytes.append(analyte)

        for analyte in self.analytes:
            analyte.normalized_data = NormalizedData(analyte,self.analytes[-1])