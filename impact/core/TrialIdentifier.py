from ..database import Base

from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from warnings import warn

class Strain(Base):
    """
    Model for a strain
    """

    __tablename__ = 'strain'

    id = Column(Integer, primary_key=True)
    nickname = Column(String)
    formal_name = Column(String)
    plasmid_1 = Column(String)
    plasmid_2 = Column(String)
    plasmid_3 = Column(String)
    parent = Column(Integer,ForeignKey('strain.id'))

    def __init__(self, name='',**kwargs):
        for key in kwargs:
            if key in ['nickname','formal_name', 'plasmid_1','plasmid_2','plasmid_3']:
                setattr(self,key,kwargs[key])
            else:
                setattr(self,key,None)

        if name != '':
            self.nickname = name
        # models.Model.__init__(self, *args, **kwargs)

    def __str__(self):
        plasmid_summ = '+'.join([plasmid
                                 for plasmid in [self.plasmid_1,self.plasmid_2,self.plasmid_3]
                                 if plasmid is not None])

        if self.nickname is None:
            nick = ''
        else:
            nick = self.nickname
        if plasmid_summ :
            return nick+'+'+plasmid_summ
        else:
            return nick

    @property
    def unique_id(self):
        return self.name

class MediaComponent(Base):
    """
    Media component many-to-many relationship
    """

    __tablename__ = 'media_component'
    id = Column(Integer,primary_key=True)
    name = Column(String,unique=True)

    def __init__(self, name):
        self.name = name

class ComponentConcentration(Base):
    """
    Concentration of all components for all media
    """
    __tablename__ = 'comp_conc'

    id = Column(Integer, primary_key=True)

    media_id = Column(String, ForeignKey('media.id'))
    media = relationship("Media", cascade='all')

    component_name = Column(String, ForeignKey('media_component.name'))
    media_component = relationship("MediaComponent", cascade='all')

    concentration = Column(Float)

    def __init__(self, component, concentration, unit=None, **kwargs):
        for key in kwargs:
            if key in ['media']:
                setattr(self,key,kwargs[key])

        self.media_component = component
        self.concentration = concentration

    def _convert_units(self):
        if not self.units_converted:
            if self._unit == '%':
                self._concentration *= 10
            elif self._unit == 'g/L':
                pass
            else:
                raise Exception('Only g/L and % supported')

class Media(Base):
    __tablename__ = 'media'
    id = Column(Integer,primary_key=True)
    nickname = Column(String)
    name = Column(String)
    component_concentrations = relationship('ComponentConcentration', cascade = 'all')
    parent = Column(Integer,ForeignKey('media.name'))

    def __init__(self, concentration=None, unit=None, **kwargs):
        for key in kwargs:
            if key in ['parent','nickname','name']:
                setattr(self,key,kwargs[key])

        self.component_concentrations = []

        self._concentration = concentration
        self._unit = unit
        self.unit_conversion_flag = False

        self.parent = None

        if concentration and unit:
            self._convert_units()

    @property
    def components(self):
        return [compconc.media_component.name for compconc in self.component_concentrations]

    def __str__(self):
        if self.parent:
            return '+'.join([item for item in
                             [compconc.concentration + 'g/L ' + compconc.media_component.name for compconc in
                              self.component_concentrations] + self.parent_name])
        else:
            return '+'.join([item for item in
                             [str(compconc.concentration) + 'g/L ' + compconc.media_component.name for compconc in
                              self.component_concentrations]])

    @property
    def unique_id(self):
        return self.name

class Environment(Base):
    __tablename__ = 'environment'

    id = Column(Integer, primary_key=True)
    labware_id = Column(Integer, ForeignKey('labware.id'))
    labware = relationship('Labware')
    shaking_speed = Column(Float)
    shaking_diameter = Column(Float,nullable=True)
    temperature = Column(Float)

    def __str__(self):
        return '%s %s %s' % (self.labware, self.shaking_speed, self.temperature)

class Labware(Base):
    __tablename__ = 'labware'

    id = Column(Integer, primary_key=True)
    name = Column(String,unique=True)

    def __str__(self):
        return self.name

class Analyte(Base):
    __tablename__ = 'analyte'

    name = Column(String, primary_key=True)
    default_type = Column(String)

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

    __tablename__ = 'trial_identifier'

    id = Column(Integer, primary_key=True)

    strain_id = Column(Integer, ForeignKey('strain.id'))
    strain = relationship("Strain")

    media_name = Column(String, ForeignKey('media.name'))
    media = relationship("Media")

    environment_id = Column(Integer, ForeignKey('environment.id'))
    environment = relationship('Environment')

    # trial specific
    replicate_id = Column(Integer)

    # analyte data specific
    analyte_name = Column(String,ForeignKey('analyte.name'))
    analyte_type = Column(String)

    id_1 = Column(String)
    id_2 = Column(String)
    id_3 = Column(String)

    def __init__(self, strain=None, media=None, environment=None):
        self.strain = Strain() if strain is None else strain
        self.media = Media() if media is None else media
        self.environment = Environment() if strain is None else environment

        # self.time = -1
        # self.replicate_id = -1
        # self.analyte_name = None

    def __str__(self):
        return "strain: %s, media: %s, env: %s, analyte: %s, t: %s, rep: %s" % (self.strain,self.media,self.environment,self.analyte_name,self.time,self.replicate_id)

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
                self.strain = Strain(nickname=tempParsedIdentifier[0])
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

    def unique_analyte_data(self):
        """
        Returns a string identifying the unique attribute of a single trial
        """
        return self.unique_single_trial() + ' ' + self.analyte_name

    def unique_single_trial(self):
        """
        Returns a string identifying the unique attribute of a single trial
        """
        return self.unique_replicate_trial() + ' ' + str(self.replicate_id)


    def unique_replicate_trial(self):
        """
        Returns a string identifying the unique attribute of a replicate trial
        """
        return ' '.join([str(getattr(self,attr))
                         for attr in ['strain','media','id_1',
                                      'id_2','id_3']
                         if str(getattr(self,attr) != '') ])

    def get_analyte_data_statistic_identifier(self):
        ti = TrialIdentifier()
        for attr in ['strain','media','id_1','id_2','id_3','analyte_name','analyte_type']:
            setattr(ti,attr,getattr(self,attr))
        return ti

    def get_replicate_trial_trial_identifier(self):
        ti = TrialIdentifier()
        for attr in ['strain','media','id_1','id_2','id_3']:
            setattr(ti,attr,getattr(self,attr))
        return ti