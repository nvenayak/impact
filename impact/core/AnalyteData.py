from .analytes import *


class FitParameter(Base):
    __tablename__ = 'fit_parameters'

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('time_course.id'))
    parameter_name = Column(String)
    parameter_value = Column(Float)

    def __init__(self, name, value):
        self.parameter_name = name
        self.parameter_value = value
