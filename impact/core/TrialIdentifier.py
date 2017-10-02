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
                    try:
                        if vals[0][key] != vals[1][key]:
                            return False
                    except KeyError:
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
    #changed the name parent to strain because it is ambiguous. strain makes more sense in this case.
    strain = Column(Integer, ForeignKey('strain.id'))

    eq_attrs = ['gene','strain']

    def __init__(self,gene=None):
        self.gene = gene

    def __str__(self):
        return str(self.gene)


class Plasmid(Base, TrialIdentifierMixin):
    __tablename__ = 'plasmid'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    strain = Column(Integer, ForeignKey('strain.id'))

    eq_attrs = ['name','strain']

    def __init__(self,name=None):
        self.name=name

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

    parent = relationship('Strain',uselist=False)
    parent_id = Column(Integer,ForeignKey('strain.id'))

    ALE_time = Column(String)
    id_1 = Column(String)
    id_2 = Column(String)

    eq_attrs = ['name','formal_name','plasmids','knockouts','parent','id_1','id_2']
    # __table_args__ = (UniqueConstraint(*eq_attrs),)

    # UniqueConstraint('name','formal_name','plasmids','knockouts','parent','id_1','id_2')
    def __init__(self, name='',**kwargs):
        self.id_1 = ''
        self.id_2 = ''

        # formal name removed from list of keys because formal name is constructed using the strain's parent, knockouts
        # and plasmids. It is not an attribute on its own. Also, plasmids was made a list arguement instead of the
        # previous implementation where each plasmid was described separately. This was done so that it is consistent
        # to the usage of plasmids everywhere else in the code.
        # TODO
        for key in kwargs:
            if key in ['name', 'plasmids', 'knockouts', 'parent','formal_name']:
                setattr(self,key,kwargs[key])
            else:
                setattr(self,key,None)

        #Build formal name from parent, knockouts and plasmids
        self.formal_name=''
        if self.parent:
            self.formal_name += self.parent.name
        #if self.name:
        self.formal_name += self.name #This is actually wrong. Proper way is to give the parent's name appropriately
        if self.knockouts:
            self.formal_name += ' \u0394('
            self.formal_name += ','.join([knockout.gene for knockout in self.knockouts])
            self.formal_name += ')'
        if self.plasmids:
            self.formal_name += ' + '
            self.formal_name += ' + '.join([plasmid.name for plasmid in self.plasmids])


        #Set name to be formal name if no explicit name is given
        if name != '':
            self.name = name
        else:
            self.name = self.formal_name

        # models.Model.__init__(self, *args, **kwargs)

    def __str__(self):
    #already built formal_name using similar code in __init__.
        return self.formal_name

    @property
    def unique_id(self):
        return self.name

    # def add_plasmid(self):


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

    #Removed media as one of the attributes. Does not make sense to have it. Component concentration is a child of media
    # and not the other way round.
    eq_attrs = ['component', 'concentration']


    def __init__(self, component, concentration, unit=' a.u.', **kwargs):
        # Marked as comments because there is no use of media as an attribute of component concentration.
        #for key in kwargs:
        #    if key in ['media']:
        #        setattr(self,key,kwargs[key])

#1 change made here: previous version had self.media_component. that is not a member of this table. It should
# instead read self.component.
        self.component = component
        self.component_name = component.name
        self.unit = unit
        self.concentration = concentration

    # Purpose of this function? Easier to pass converted units into the parser than do this
    #def _convert_units(self):
    #    if not self.units_converted:
    #        if self._unit == '%':
    #            self._concentration *= 10
    #        elif self._unit == 'g/L':
    #            pass
    #        else:
    #            raise Exception('Only g/L and % supported')


class Media(Base, TrialIdentifierMixin):
    __tablename__ = 'media'
    id = Column(Integer,primary_key=True)
    name = Column(String, nullable=True)
    formal_name = Column(String, nullable=True)

    # the class media_component as well)
    components = relationship('ComponentConcentration',
                              collection_class=attribute_mapped_collection('component_name'),
                              cascade = 'all')

    parent = relationship('Media', uselist=False)
    parent_id = Column(Integer,ForeignKey('media.id'), nullable=True)

    # unit = Column(String)

    # formal name removed from list of keys because formal name is constructed using the strain's parent, knockouts
    # and plasmids. It is not an attribute on its own.
    eq_attrs = ['name', 'components', 'parent']


    #What is this concentration for?
    def __init__(self, concentration=None, unit='a.u.', name='', **kwargs):
        self.parent = None
        self.name = name
        self.formal_name=''
        for key in kwargs:
            if key in ['parent','name','components']:
                setattr(self,key,kwargs[key])

        self._concentration = concentration
        # Build formal name from parent, knockouts and plasmids
        self.formal_name = ''
        if self.parent:
            self.formal_name += self.parent.name
        elif self.name:
            self.formal_name += self.name #This is wrong. Right way is to pass parent
        if self.components:
            for component in self.components:
                self.formal_name += ' + '
                self.formal_name += str(self.components[component].concentration)
                self.formal_name += self.components[component].unit + ' '
                self.formal_name += self.components[component].component_name

        if not self.name:
            self.name=self.formal_name


        # self.unit = unit
        # above line was commented because it does not make sense here. unit is an attribute of the class component_concentration
        # self.unit_conversion_flag = False

        # if concentration and unit:
        #     self._convert_units()

    #Everything that needs to go on here is already assigned to self.formal_name
    def __str__(self):
        return self.formal_name

    @property
    def unique_id(self):
        return self.name

    def add_component(self, component, concentration=None, unit=' a.u.'):
        if isinstance(component, ComponentConcentration):
            # If the component is fully formed
            self.components[component.component_name] = component
        elif concentration is not None:
            if isinstance(component,MediaComponent):
                self.components[component.name] = ComponentConcentration(component, concentration, unit)
            elif isinstance(component,str):
                # If only a name was given
                self.components[component] = ComponentConcentration(MediaComponent(component), concentration, unit)
        else:
            raise Exception('Component added with no concentration')

class Environment(Base, TrialIdentifierMixin):
    __tablename__ = 'environment'

    id = Column(Integer, primary_key=True)
    labware_id = Column(Integer, ForeignKey('labware.id'))
    labware = relationship('Labware')
    shaking_speed = Column(Float)
    shaking_diameter = Column(Float,nullable=True)
    temperature = Column(Float)
    pH = Column(Float)
    DO = Column(Float)

    eq_attrs = ['labware', 'shaking_speed', 'shaking_diameter', 'temperature', 'pH', 'DO']

    # @reconstructor
    def __init__(self, labware=None, **kwargs):
        self.labware = Labware() if labware is None else labware
        # Overwrite user-set parameters
        for arg in kwargs:
            setattr(self,arg,kwargs[arg])

    def __str__(self):
        env = ''
        if self.labware:
            env += str(self.labware)+' '
        if self.shaking_speed:
            env += str(self.shaking_speed)+'RPM '
        if self.shaking_diameter:
            env += str(self.shaking_diameter)+' mm Shaking Diameter'
        if self.temperature:
            env += str(self.temperature)+'\u00B0C '
        if self.pH:
            env += 'pH: ' + str(self.pH) + ' '
        if self.DO:
            env += 'DO: ' + str(self.DO) + ' '
        return env


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

    #What are these?
    id_1 = Column(String)
    id_2 = Column(String)
    id_3 = Column(String)

    eq_attrs = ['strain','media','environment','id_1','id_2','id_3']

    # @reconstructor
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

    def summary(self, items):
        summary = dict()
        for item in items:
            summary[item] = getattr(self, item)
        return summary

    def parse_identifier(self, id):
        parameter_values=id.split('|')
        identifier_dict={'strain':{'name':'','plasmid':[],'ko':[],'parent':''},
                            'media':{'name':'','cc':{},'parent':''},
                            'environment':{'labware':'','shaking_speed':'','shaking_diameter':'','temperature':'',
                                           'pH':'','DO':''}}

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
                        if key in ['strain', 'media']:
                            identifier_dict[key]['name'] = val.strip()
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
                            if attr2 == 'parent':
                                identifier_dict[attr1][attr2]=val.strip()
                            if attr2 == 'ko':
                                kos = val.split(',')
                                for ko in kos:
                                    identifier_dict[attr1][attr2].append(Knockout(gene=ko.strip()))
                            if attr2 == 'plasmid':
                                plasmids = val.split(',')
                                for plasmid in plasmids:
                                    identifier_dict[attr1][attr2].append(Plasmid(name=plasmid.strip()))
                            #if attr2 == 'id':
                            #    if self.strain.id_1 == '':
                            #        self.strain.id_1 = val
                            #    elif self.strain.id_2 == '':
                            #        self.strain.id_2 = val
                            #    else:
                            #        raise Exception('Only two generic strain ids permitted')

                        # Set component concentrations
                        elif attr1 == 'media':
                            if attr2 == 'cc':
                                compconcs=val.split(',')
                                cclist=[]
                                for compconc in compconcs:
                                    if(len(compconc.split(' '))==2):
                                        # if units are not given in the identifier
                                        conc, comp = compconc.split(' ')
                                        try:
                                            # Try format concentration component (0.2 glc)
                                            cclist.append(
                                                ComponentConcentration(component=MediaComponent(comp),concentration=float(conc)))
                                        except ValueError:
                                            # Try format component concentration (glc 0.2)
                                            cclist.append(
                                                ComponentConcentration(component=MediaComponent(conc), concentration=float(comp)))

                                    elif(len(val.split(' '))==3):
                                        #if units are given in the identifier
                                        conc,unit,comp = val.split(' ')
                                        try:
                                            # Try format concentration component (0.2 glc mM)
                                            cclist.append(
                                                ComponentConcentration(component=MediaComponent(comp),concentration=float(conc),unit=' '+unit))
                                        except ValueError:
                                            # Try format component concentration (glc 0.2 mM)
                                            cclist.append(
                                                ComponentConcentration(component=MediaComponent(conc), concentration=float(unit),unit=' '+comp))
                                    else:
                                        raise Exception ('Unknown format for component concentration')
                                for comp in cclist:
                                    identifier_dict[attr1][attr2][comp.component_name]=comp

                            elif attr2 == 'base':
                                identifier_dict[attr1]['parent'] = val.strip()
                            else:
                                raise Exception ('Unknown attribute passed for media identifier')


                        elif attr1 == 'environment':
                            if attr2 =='labware':
                                identifier_dict[attr1][attr2]=Labware(val.strip())
                            elif attr2 in ['shaking_speed','shaking_diameter','temperature','pH','DO']:
                                try:
                                    identifier_dict[attr1][attr2]=float(val.strip())
                                except ValueError:
                                    print('Invalid value entered for attribute')
                            else:
                                raise Exception ('Unkown attribute passed for environment identifier')
                        else:
                            # Set other attrs
                            setattr(getattr(self, attr1), attr2, val)
                    else:
                        raise Exception('Too many subparameters traversed' + str(key))
                else:
                    raise Exception('Malformed parameter: '+id)

        if identifier_dict['strain']['parent']:
            self.strain=Strain(name=identifier_dict['strain']['name'],plasmids=identifier_dict['strain']['plasmid'],
                           knockouts=identifier_dict['strain']['ko'],parent=Strain(name=identifier_dict['strain']['parent']))
        else:
            self.strain = Strain(name=identifier_dict['strain']['name'], plasmids=identifier_dict['strain']['plasmid'],
                                 knockouts=identifier_dict['strain']['ko'],)
        if identifier_dict['media']['parent']:
            self.media=Media(name=identifier_dict['media']['name'],parent=Media(name=identifier_dict['media']['parent']),
                         components=identifier_dict['media']['cc'])
        else:
            self.media = Media(name=identifier_dict['media']['name'],
                               components=identifier_dict['media']['cc'])
        self.environment=Environment(labware=identifier_dict['environment']['labware'],
                                    shaking_speed=identifier_dict['environment']['shaking_speed'],
                                     shaking_diameter=identifier_dict['environment']['shaking_diameter'],
                                     temperature=identifier_dict['environment']['temperature'],
                                     pH=identifier_dict['environment']['pH'],DO=identifier_dict['environment']['DO'])


        # parameter_values = id.split('|')
        # old version commented
        # for parameter_value in parameter_values:
        #     if parameter_value != '':
        #         if len(parameter_value.split(':')) == 1:
        #             if parameter_value in ['blank','Blank']:
        #                 self.blank = True
        #             else:
        #                 raise Exception('Identifier malformed: '+parameter_value)
        #         elif len(parameter_value.split(':')) == 2:
        #             key, val = parameter_value.split(':')
        #
        #             if len(key.split('__')) == 1:
        #                 if key in ['strain', 'media', 'environment']:
        #                     getattr(self, key).name = val.strip()
        #                 elif key == 'rep':
        #                     self.replicate_id = int(val)
        #                 elif key in ['time','t']:
        #                     self.time = float(val)
        #                 else:
        #                     raise Exception('Unknown key: ' + str(key))
        #             elif len(key.split('__')) == 2:
        #                 attr1, attr2 = key.split('__')
        #
        #                 # Set knockouts
        #                 if attr1 == 'strain':
        #                     if attr2 == 'ko':
        #                         kos = val.split(',')
        #                         for ko in kos:
        #                             self.strain.knockouts.append(Knockout(gene=ko))
        #                     if attr2 == 'plasmids':
        #                         plasmids = val.split(',')
        #                         for plasmid in plasmids:
        #                             self.strain.plasmids.append(Plasmid(name=plasmid))
        #                     if attr2 == 'id':
        #                         if self.strain.id_1 == '':
        #                             self.strain.id_1 = val
        #                         elif self.strain.id_2 == '':
        #                             self.strain.id_2 = val
        #                         else:
        #                             raise Exception('Only two generic strain ids permitted')
        #
        #                 # Set component concentrations
        #                 elif attr1 == 'media':
        #                     if attr2 == 'cc':
        #                         conc, comp = val.split(' ')
        #                         try:
        #                             # Try format concentration component (0.2 glc)
        #                             self.media.add_component(ComponentConcentration(MediaComponent(comp), float(conc)))
        #                         except ValueError:
        #                             # Try format component concentration (glc 0.2)
        #                             self.media.add_component(ComponentConcentration(MediaComponent(conc), float(comp)))
        #                     elif attr2 == 'base':
        #                         self.media.parent = Media(name=val)
        #                     else:
        #                         setattr(self.media,attr2,val)
        #
        #
        #                 elif attr1 == 'environment':
        #                     if attr2 == 'labware':
        #                         self.environment.labware.name = val
        #                     elif attr2 in ['shaking_speed','temperature','pH','DO']:
        #                         setattr(self.environment,attr2,float(val))
        #                     else:
        #                         setattr(self.environment,attr2,val)
        #                 else:
        #                     # Set other attrs
        #                     setattr(getattr(self, attr1), attr2, val)
        #             else:
        #                 raise Exception('Too many subparameters traversed' + str(key))
        #         else:
        #             raise Exception('Malformed parameter: '+id)

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


        return ' '.join([str(getattr(self, attr))
                         for attr in ['strain', 'media', 'environment', 'id_1',
                                      'id_2', 'id_3']
                         if str(getattr(self, attr) != '')])

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

