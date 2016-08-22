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

# If in the iPython environment, initialize notebook mode
try:
    temp = __IPYTHON__
except NameError:
    pass
else:
    import plotly
    plotly.offline.init_notebook_mode()

def init_db(db_name):
    """
    Initialize the database given a database file path.

    Parameters
    ----------
    db_name : str
        The path of the database, or name if it is in working directory
    """

    # Initialize database
    conn = sql.connect(db_name)
    c = conn.cursor()

    c.execute("""\
       CREATE TABLE IF NOT EXISTS experimentTable
       (experiment_id INTEGER PRIMARY KEY, import_date TEXT, experiment_title TEXT,
       experiment_start_date TEXT, experiment_end_date TEXT, primary_scientist_name TEXT,
       secondary_scientist_name TEXT, medium_base TEXT, medium_supplements TEXT, notes TEXT)
    """)

    c.execute("""\
       CREATE TABLE IF NOT EXISTS replicateTable
         (replicateID INTEGER PRIMARY KEY, experiment_id INT,
          strain_id TEXT, id_1 TEXT, id_2 TEXT, id_3 TEXT,
          FOREIGN KEY(experiment_id) REFERENCES experimentTable(experiment_id))
    """)

    for suffix in ['', '_avg', '_std']:
        c.execute("""\
           CREATE TABLE IF NOT EXISTS singleTrialTable""" + suffix + """
           (singleTrialID""" + suffix + """ INTEGER PRIMARY KEY, replicateID INT, replicate_id INT, yieldsDict BLOB,
           FOREIGN KEY(replicateID) REFERENCES replicateTable(replicateTable))
        """)

        c.execute("""\
           CREATE TABLE IF NOT EXISTS timeCourseTable""" + suffix + """
           (timeCourseID INTEGER PRIMARY KEY, singleTrial""" + suffix + """ID INTEGER,
           titerType TEXT, analyte_name TEXT, time_vector BLOB, data_vector BLOB, rate BLOB,
           FOREIGN KEY(singleTrial""" + suffix + """ID) REFERENCES singleTrialID(singleTrialTable""" + suffix + """))
        """)

    conn.commit()
    c.close()
    conn.close()



