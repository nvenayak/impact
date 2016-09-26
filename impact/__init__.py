__author__ = 'Naveen Venayak'

import copy
import sqlite3 as sql
import sys
import time

from matplotlib import pyplot
try:
    from pyexcel_xlsx import get_data
except ImportError as e:
    print('Could not import pyexcel')
    print(e)
    pass

if sys.version_info.major < 3:
    raise Exception('Require Python >= 3.5')
elif sys.version_info.minor < 5:
    raise Exception('Require Python >= 3.5')

import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt

import dill as pickle

from .TimePoint import TimePoint
from .AnalyteData import TimeCourse
from .TrialIdentifier import TrialIdentifier
from .SingleTrial import SingleTrial
from .ReplicateTrial import ReplicateTrial
from .Experiment import Experiment
from .Project import Project
from .plotting import *
from .database import *

# If in the iPython environment, initialize notebook mode
try:
    temp = __IPYTHON__
except NameError:
    pass
else:
    import plotly
    plotly.offline.init_notebook_mode()



