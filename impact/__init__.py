__author__ = 'Naveen Venayak'

import sys
import os
from warnings import warn

if sys.version_info.major < 3:
    warn(Exception('Require Python >= 3.5'))
elif sys.version_info.minor < 5:
    warn(Exception('Require Python >= 3.5'))

# Django ORM support
# Add impact_cloud path and init django
# import django
#
# def start_db_engine():
#     BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#     sys.path.append(os.path.join(BASE_DIR, '../impact_cloud'))
#     os.environ["DJANGO_SETTINGS_MODULE"] = "impact_main_site.settings"
#     django.setup()

# Import the core classes
from .database import Base
from .core.TrialIdentifier import *
from .core.AnalyteData import TimeCourse, TimePoint
from .core.SingleTrial import SingleTrial
from .core.ReplicateTrial import ReplicateTrial
from .core.Experiment import Experiment
from .core.Project import Project
from .core.settings import settings

from sqlalchemy import create_engine

def bind_engine(echo=False):
    engine = create_engine('sqlite:///test_impact.db', echo=echo)
    return engine

def create_session():
    from sqlalchemy.orm import sessionmaker

    engine = bind_engine()

    session_maker = sessionmaker(bind=engine)
    return session_maker()

try:
    os.remove('test_impact.db')
except FileNotFoundError:
    pass

engine = bind_engine()
Base.metadata.create_all(engine)
