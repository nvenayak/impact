# from django.db import models

# class BaseClass(models.Model):
#     class Meta:
#         app_label = 'impact'


from sqlalchemy import Column, Integer, String, ForeignKey, Float, Table
from ..database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.orm.collections import attribute_mapped_collection


class Strain(Base):
    """
    Identifies the strain used
    """
    # django orm declarations
    # class Meta:
    #     app_label = 'impact'
    #
    # strain_name = models.CharField(max_length=30)
    # plasmid_1 = models.CharField(max_length=15)
    # plasmid_2 = models.CharField(max_length=15)
    # plasmid_3 = models.CharField(max_length=15)
    __tablename__ = 'strain'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    plasmid_1 = Column(String)
    plasmid_2 = Column(String)
    plasmid_3 = Column(String)

    def __init__(self, *args, **kwargs):
        # models.Model.__init__(self, *args, **kwargs)

        self.name = ''    # 'E. coli MG1655'
        self.plasmid_1 = None       # ptrc99a
        self.plasmid_2 = None       # ptrc99a
        self.plasmid_3 = None       # ptrc99a

    def __str__(self):
        plasmid_summ = '+'.join([plasmid
                                 for plasmid in [self.plasmid_1,self.plasmid_2,self.plasmid_3]
                                 if plasmid is not None])
        if plasmid_summ :
            return self.name+'+'+plasmid_summ
        else:
            return self.name


    @property
    def unique_id(self):
        return self.name

class MediaComponent(Base):
    """
    Media component many-to-many relationship
    """

    __tablename__ = 'media_components'
    name = Column(String,primary_key=True)
    # BiGG_id = Column(String,primary_key=True)

    def __init__(self, name):
        self.name = name

class ComponentConcentration(Base):
    """
    Concentration of all components for all media
    """
    __tablename__ = 'comp_conc'

    media_name = Column(String, ForeignKey('media.name'), primary_key=True)
    component_name = Column(String, ForeignKey('media_components.name'), primary_key=True,)
    # media_component = relationship("")
    concentration = Column(Float)
    media_component = relationship("MediaComponent", cascade='all')
    media = relationship("Media", cascade='all')

    def __init__(self, component, concentration, unit=None):
        self.media_component = component
        self.concentration = concentration

    def _convert_units(self):
        if not self.units_converted:
            if self._unit == '%':
                self._concentration = self._concentration*10
            elif self._unit == 'g/L':
                pass
            else:
                raise Exception('Only g/L and % supported')

class Media(Base):
    __tablename__ = 'media'
    name = Column(String, primary_key=True)
    component_concentrations = relationship('ComponentConcentration', cascade = 'all')
    parent = Column(Integer,ForeignKey('media.name'))

    def __init__(self, name = 'NA', concentration=None, unit=None):
        self.components = []
        self.component_concentrations = []
        self.name = name  # M9

        self._concentration = concentration
        self._unit = unit
        self.unit_conversion_flag = False

        self.parent = None

        if concentration and unit:
            self._convert_units()

    def __str__(self):
        component_names = [compconc.component_name for compconc in self.component_concentrations]
        if self.parent:
            parent_name = self.parent.name
        else:
            parent_name = ''
        return '+'.join([item for item in component_names+parent_name])

    @property
    def unique_id(self):
        return self.name


    # @property
    # def unit(self):
    #     return self._unit
    #
    # @unit.setter
    # def unit(self, unit):
    #     if self._
    #     if self._concentration:
    #         self._unit = unit
    #         self._convert_units()
    #     else:
    #

class Analyte(Base):
    __tablename__ = 'analyte'

    name = Column(String, primary_key=True)

class TrialIdentifier(Base):
    """
    Carries information about the run through all the objects

    Attributes
    -----------
    strain.name : str
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
    ###########################
    # Django ORM stuff
    # id = models.AutoField(primary_key=True)
    #
    # first_name = models.CharField(max_length=30)
    # last_name = models.CharField(max_length=30)
    #
    # strain.name = models.CharField(max_length=30)
    # id_1 = models.CharField(max_length=30)
    # id_2 = models.CharField(max_length=30)
    # id_3 = models.CharField(max_length=30)
    #
    # replicate_id = models.IntegerField()
    #
    # analyte_name = models.CharField(max_length=30)
    # _analyte_type = models.CharField(max_length=30)
    #
    #
    # class Meta:
    #     app_label = 'impact'
    #     db_table = 'trial_identifier'
    #     _DATABASE = 'impact'
    ###########################


    # SQL alchemy
    __tablename__ = 'trial_identifier'

    id = Column(Integer, primary_key=True)

    strain_id = Column(Integer, ForeignKey('strain.id'))
    strain = relationship("Strain")

    media_name = Column(String, ForeignKey('media.name'))
    media = relationship("Media")

    # trial specific
    replicate_id = Column(Integer)

    # analyte data specific
    analyte_name = Column(String,ForeignKey('analyte.name'))
    analyte_type = Column(String)

    # relationships = relationship('TimeCourse', back_populates='_trial_identifier', uselist=False)

    def __init__(self, strain=Strain(), media=Media(), strain_name='', id_1='', id_2='', id_3='',
                 replicate_id = None, time = -1, analyte_name = 'None',
                 analyte_type = 'None', *args, **kwargs):

        # models.Model.__init__(self, *args, **kwargs)

        self.strain = strain       # e.g. MG1655 dlacI
        self.media = media
        self.strain.name = strain_name

        self.id_1 = id_1
        self.id_2 = id_2
        self.id_3 = id_3

        self.replicate_id = replicate_id    # e.g. 1

        self.time = time                    # e.g. 0

        self.analyte_name = analyte_name    # BiGG id preferred. E.g. ac, succ, pyr, glc__D
        self._analyte_type = analyte_type   # e.g. substrate, product, biomass

    # @property
    # def strain.name(self):
    #     return self._strain.name# .__str__()#summary()
    #
    # @strain.name.setter
    # def strain.name(self, strain.name):
    #     self._strain.name.name = strain.name

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

    # def save(self, *args, **kwargs):
    #     """
    #     Overrides the save function to also save all children to the db.
    #     """
    #
    #     self.media_id.save()
    #     self.strain.name.save()
    #     models.Model.save(self, *args, **kwargs)

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
            a comma-separated string containing a TrialIdentifier in standard form - strain.name,id_1,id_2,replicate_id
        """
        if type(csv_trial_identifier) is str:
            tempParsedIdentifier = csv_trial_identifier.split(',')
            if len(tempParsedIdentifier) == 0:
                print(tempParsedIdentifier, " <-- not processed")
            if len(tempParsedIdentifier) > 0:
                print(tempParsedIdentifier[0])
                self.strain.name = tempParsedIdentifier[0]
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
        return str(self.strain) + self.id_1 + self.id_1 + str(self.replicate_id) + self.analyte_name + self.analyte_type

    def get_unique_id_for_ReplicateTrial(self):
        """
        Get the unique information for a single replicate_id
        Returns
        -------
        unique_id : str
            Unique id defining a replicate_id.
        """
        return str(self.strain) + self.id_1 + self.id_2

        # def return_unique_experiment_id(self):
        #     return self.strain.name + self.id_1 + self.id_2 + str(self.replicate_id)

str