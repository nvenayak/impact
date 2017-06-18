from ..database import Base, create_session

from sqlalchemy import Column, Integer, String, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import relationship, reconstructor
from warnings import warn
from sqlalchemy.orm.collections import attribute_mapped_collection

class TrialIdentifierMixin(object):
    # eq_attrs = []
    # __table_args__ = (UniqueConstraint(*eq_attrs),)

    def __eq__(self, other):
        if not isinstance(other,self.__class__):
            return False

        for attr in self.eq_attrs:
            vals = [getattr(self,attr), getattr(other,attr)]
            if not hasattr(vals[0],'__len__') or isinstance(vals[0],str):
                if vals[0] != vals[1]:
                    return False
            elif isinstance(vals[0],list):
                for item1, item2 in zip(vals[0],vals[1]):
                    if item1 != item2:
                        return False
            elif isinstance(vals[0],dict):
                for key in vals[0]:
                    if vals[0][key] != vals[1][key]:
                        return False
            else:
                raise Exception('Object contains non-hashable')
        return True

    def __hash__(self):
        cat_hash = []
        for attr in self.eq_attrs:
            val = getattr(self,attr)
            if isinstance(val,list):
                cat_hash += val
            elif isinstance(val,dict):
                keys = sorted(list(val.keys()))
                cat_hash += [val[key] for key in keys]
            else:
                try:
                    cat_hash.append(val)
                except Exception as e:
                    print('Object contains non-hashable')
                    raise Exception(e)

        return hash(tuple(cat_hash))


class Knockout(Base, TrialIdentifierMixin):
    __tablename__ = 'knockout'
    id = Column(Integer, primary_key=True)
    gene = Column(String)
    parent = Column(Integer, ForeignKey('strain.id'))

    eq_attrs = ['gene','parent']

    def __str__(self):
        return str(self.gene)


class Plasmid(Base, TrialIdentifierMixin):
    __tablename__ = 'plasmid'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    strain = Column(Integer, ForeignKey('strain.id'))

    eq_attrs = ['name','strain']

    def __str__(self):
        return str(self.name)


class Strain(Base, TrialIdentifierMixin):
    """
    Model for a strain
    """

    __tablename__ = 'strain'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    formal_name = Column(String)
    plasmids = relationship('Plasmid')
    knockouts = relationship('Knockout')
    parent = Column(Integer,ForeignKey('strain.id'))
    id_1 = Column(String)
    id_2 = Column(String)

    eq_attrs = ['name','formal_name','plasmids','knockouts','parent','id_1','id_2']
    # __table_args__ = (UniqueConstraint(*eq_attrs),)

    # UniqueConstraint('name','formal_name','plasmids','knockouts','parent','id_1','id_2')
    def __init__(self, name='',**kwargs):
        self.id_1 = ''
        self.id_2 = ''

        for key in kwargs:
            if key in ['name','formal_name', 'plasmid_1','plasmid_2','plasmid_3']:
                setattr(self,key,kwargs[key])
            else:
                setattr(self,key,None)

        if name != '':
            self.name = name
        # models.Model.__init__(self, *args, **kwargs)

    def __str__(self):
        plasmid_summ = '+'.join([str(plasmid) for plasmid in self.plasmids])

        if self.name is None:
            name = ''
        else:
            name = self.name

        summ_id = ''
        if self.id_1 != '': summ_id = summ_id+' '+self.id_1
        if self.id_2 != '': summ_id = summ_id+' '+self.id_2

        knockouts = 'd('+','.join([str(ko) for ko in self.knockouts])+')' if self.knockouts else ''

        if plasmid_summ :
            return name+'+'+plasmid_summ+summ_id+knockouts
        else:
            return name+summ_id+knockouts

    @property
    def unique_id(self):
        return self.name


class MediaComponent(Base, TrialIdentifierMixin):
    """
    Media component many-to-many relationship
    """

    __tablename__ = 'media_component'
    id = Column(Integer,primary_key=True)
    name = Column(String,unique=True)

    eq_attrs = ['name']

    def __init__(self, name):
        self.name = name


class ComponentConcentration(Base, TrialIdentifierMixin):
    """
    Concentration of all components for all media
    """
    __tablename__ = 'comp_conc'

    id = Column(Integer, primary_key=True)

    media_id = Column(String, ForeignKey('media.id'))
    media = relationship("Media", cascade='all')

    component_name = Column(String, ForeignKey('media_component.name'))
    component = relationship("MediaComponent", cascade='all')

    concentration = Column(Float)

    eq_attrs = ['media','component','concentration']


    def __init__(self, component, concentration, unit=None, **kwargs):
        for key in kwargs:
            if key in ['media']:
                setattr(self,key,kwargs[key])

        self.media_component = component
        self.component_name = component.name

        self.concentration = concentration

    def _convert_units(self):
        if not self.units_converted:
            if self._unit == '%':
                self._concentration *= 10
            elif self._unit == 'g/L':
                pass
            else:
                raise Exception('Only g/L and % supported')


class Media(Base, TrialIdentifierMixin):
    __tablename__ = 'media'
    id = Column(Integer,primary_key=True)
    name = Column(String)
    formal_name = Column(String)
    components = relationship('ComponentConcentration',
                              collection_class=attribute_mapped_collection('component_name'),
                              cascade = 'all')

    parent = Column(Integer,ForeignKey('media.name'))

    eq_attrs = ['name', 'formal_name', 'components', 'parent']


    def __init__(self, concentration=None, unit=None, **kwargs):
        for key in kwargs:
            if key in ['parent','name','name']:
                setattr(self,key,kwargs[key])

        self._concentration = concentration
        self._unit = unit
        self.unit_conversion_flag = False

        self.parent = None

        if concentration and unit:
            self._convert_units()

    def __str__(self):
        if self.parent:
            return self.parent.name+'+'+'+'.join([item for item in
                             [str(cc.concentration) + 'g/L ' + cc.media_component.name for cc in
                              self.components.values()]])
        else:
            return '+'.join([item for item in
                             [str(cc.concentration) + 'g/L ' + cc.media_component.name for cc in
                              self.components.values()]])

    @property
    def unique_id(self):
        return self.name

    def add_component(self, component, concentration=None, unit=None):
        if isinstance(component,MediaComponent):
            if concentration is not None:
                self.components[component.name] = ComponentConcentration(component, concentration, unit)
            else:
                raise Exception('Component added with no concentration')
        elif isinstance(component,ComponentConcentration):
            # If the component is fully formed
            self.components[component.component_name] = component
        elif isinstance(component,str):
            # If only a name was given
            self.components[component.name] = ComponentConcentration(MediaComponent(component), concentration, unit)


class Environment(Base, TrialIdentifierMixin):
    __tablename__ = 'environment'

    id = Column(Integer, primary_key=True)
    labware_id = Column(Integer, ForeignKey('labware.id'))
    labware = relationship('Labware')
    shaking_speed = Column(Float)
    shaking_diameter = Column(Float,nullable=True)
    temperature = Column(Float)

    eq_attrs = ['labware', 'shaking_speed', 'shaking_diameter', 'temperature']

    # @reconstructor
    def __init__(self, labware=None):
        self.labware = Labware() if labware is None else labware

    def __str__(self):
        _ = ''
        if self.labware is not None:
            _ += str(self.labware)+' '
        if self.shaking_speed is not None:
            _ += str(self.shaking_speed)+'RPM '
        if self.temperature is not None:
            _ += str(self.temperature)+'C'
        return _ #'%s %sRPM %sC' % (self.labware, self.shaking_speed, self.temperature)


class Labware(Base, TrialIdentifierMixin):
    __tablename__ = 'labware'

    id = Column(Integer, primary_key=True)
    name = Column(String,unique=True)

    eq_attrs = ['name']

    def __init__(self, name=None):
        self.name = name

    def __str__(self):
        return str(self.name)


class Analyte(Base, TrialIdentifierMixin):
    __tablename__ = 'analyte'

    name = Column(String, primary_key=True)
    default_type = Column(String)

    eq_attrs = ['name']


class ReplicateTrialIdentifier(Base, TrialIdentifierMixin):
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

    __tablename__ = 'replicate_trial_identifier'

    id = Column(Integer, primary_key=True)

    strain_id = Column(Integer, ForeignKey('strain.id'))
    strain = relationship("Strain")

    media_name = Column(String, ForeignKey('media.name'))
    media = relationship("Media")

    environment_id = Column(Integer, ForeignKey('environment.id'))
    environment = relationship('Environment')

    id_1 = Column(String)
    id_2 = Column(String)
    id_3 = Column(String)

    eq_attrs = ['strain','media','environment','id_1','id_2','id_3']

    @reconstructor
    def __init__(self, strain=None, media=None, environment=None):
        self.strain = Strain() if strain is None else strain
        self.media = Media() if media is None else media
        self.environment = Environment() if strain is None else environment

        for var in ['id_1','id_2','id_3']:
            setattr(self,var,'')

        self.time = -1
        self.replicate_id = -1
        self.analyte_name = None

    def __str__(self):
        return "strain: %s,\tmedia: %s,\tenv: %s" % (self.strain,self.media,self.environment)
        # return "strain: %s,\tmedia: %s,\tenv: %s,\tanalyte: %s,\tt: %sh,\trep: %s" % (self.strain,self.media,self.environment,self.analyte_name,self.time,self.replicate_id)

    def summary(self, items):
        summary = dict()
        for item in items:
            summary[item] = getattr(self, item)
        return summary

    def parse_identifier(self, id):
        # Split by |
        parameter_values = id.split('|')

        for parameter_value in parameter_values:
            if parameter_value != '':
                if len(parameter_value.split(':')) == 1:
                    if parameter_value in ['blank','Blank']:
                        self.blank = True
                    else:
                        raise Exception('Identifier malformed: '+parameter_value)
                elif len(parameter_value.split(':')) == 2:
                    key, val = parameter_value.split(':')

                    if len(key.split('__')) == 1:
                        if key in ['strain', 'media', 'environment']:
                            getattr(self, key).name = val
                        elif key == 'rep':
                            self.replicate_id = int(val)
                        elif key in ['time','t']:
                            self.time = float(val)
                        else:
                            raise Exception('Unknown key: ' + str(key))
                    elif len(key.split('__')) == 2:
                        attr1, attr2 = key.split('__')

                        # Set knockouts
                        if attr1 == 'strain':
                            if attr2 == 'ko':
                                kos = val.split(',')
                                for ko in kos:
                                    self.strain.knockouts.append(Knockout(gene=ko))
                            if attr2 == 'plasmid':
                                self.strain.plasmids.append(Plasmid(name=val))
                            if attr2 == 'id':
                                if self.strain.id_1 == '':
                                    self.strain.id_1 = val
                                elif self.strain.id_2 == '':
                                    self.strain.id_2 = val
                                else:
                                    raise Exception('Only two generic strain ids permitted')

                        # Set component concentrations
                        elif attr1 == 'media':
                            if attr2 == 'cc':
                                conc, comp = val.split(' ')
                                try:
                                    # Try format concentration component (0.2 glc)
                                    self.media.add_component(ComponentConcentration(MediaComponent(comp), float(conc)))
                                except ValueError:
                                    # Try format component concentration (glc 0.2)
                                    self.media.add_component(
                                        ComponentConcentration(MediaComponent(conc), float(comp)))
                            elif attr2 == 'base':
                                self.media.parent = Media(name=val)
                            else:
                                setattr(self.media,attr2,val)


                        elif attr1 == 'environment':
                            if attr2 == 'labware':
                                self.environment.labware.name = val
                            elif attr2 in ['shaking_speed','temperature']:
                                setattr(self.environment,attr2,float(val))
                            else:
                                setattr(self.environment,attr2,val)
                        else:
                            # Set other attrs
                            setattr(getattr(self, attr1), attr2, val)
                    else:
                        raise Exception('Too many subparameters traversed' + str(key))
                else:
                    raise Exception('Malformed parameter: '+id)

    def parse_trial_identifier_from_csv(self, csv_trial_identifier):
        """
        Used to parse a CSV trial_identifier

        Parameters
        ----------
        csv_trial_identifier : str
            a comma-separated string containing a ReplicateTrialIdentifier in standard form - strain.name,id_1,id_2,replicate_id
        """
        if type(csv_trial_identifier) is str:
            tempParsedIdentifier = csv_trial_identifier.split(',')
            if len(tempParsedIdentifier) == 0:
                print(tempParsedIdentifier, " <-- not processed")
            if len(tempParsedIdentifier) > 0:
                self.strain = Strain(name=tempParsedIdentifier[0])
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

    def unique_time_point(self):
        return self.unique_single_trial()+' '+self.analyte_name

    def unique_analyte_data(self):
        """
        Returns a string identifying the unique attribute of a single trial
        """
        if self.analyte_name:
            an = self.analyte_name
        else:
            an = ''

        return self.unique_single_trial() + ' ' + an

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
                         for attr in ['strain','media','environment','id_1',
                                      'id_2','id_3']
                         if str(getattr(self,attr) != '') ])

    def get_analyte_data_statistic_identifier(self):
        ti = TimeCourseIdentifier()
        for attr in ['strain','media','environment','id_1','id_2','id_3','analyte_name','analyte_type']:
            setattr(ti,attr,getattr(self,attr))
        return ti

    def get_replicate_trial_trial_identifier(self):
        ti = ReplicateTrialIdentifier()
        for attr in ['strain','media','environment','id_1','id_2','id_3']:
            setattr(ti,attr,getattr(self,attr))
        return ti

class SingleTrialIdentifier(ReplicateTrialIdentifier):
    __tablename__ = 'single_trial_identifier'

    # replicate_trial_identifier_id = Column(Integer,ForeignKey('replicate_trial_identifier.id'))
    id = Column(Integer, ForeignKey('replicate_trial_identifier.id'), primary_key=True)
    replicate_id = Column(Integer)

    def __str__(self):
        return "strain: %s,\tmedia: %s,\tenv: %s,\tt: %sh,\trep: %s" % (self.strain,self.media,self.environment,self.time,self.replicate_id)

class TimeCourseIdentifier(SingleTrialIdentifier):
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

    __tablename__ = 'time_course_identifier'
    # single_trial_identifier_id = Column(Integer,ForeignKey('single_trial_identifier.id'))

    id = Column(Integer, ForeignKey('single_trial_identifier.id'), primary_key=True)

    analyte_name = Column(String,ForeignKey('analyte.name'))
    analyte_type = Column(String)

    def __str__(self):
        return "strain: %s,\tmedia: %s,\tenv: %s,\tanalyte: %s,\trep: %s" % (self.strain,self.media,self.environment,self.analyte_name,self.replicate_id)

