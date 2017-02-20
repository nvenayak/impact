# coding=utf-8
import sqlite3 as sql

# from sqlalchemy.ext.declarative import declarative_base
# Base = declarative_base()
#
# from sqlalchemy import create_engine
#
#
#
#
# engine = create_engine('sqlite:///:memory:', echo=True)


from django.db import models
import pandas as pd
import json

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# class PandasField(models.TextField):
#     description = 'Field to save pandas objects (df or series) as serialized JSON strings'
#
#     def __init__(self, *args, **kwargs):
#         super(PandasField, self).__init__(*args, **kwargs)
#
#     def from_db_value(self, value, expression, connection, context):
#         return pd.read_json(value)
#
#     def value_to_string(self, obj):
#         return str(obj.to_json())
#
#
# class JSONSerializableField(models.TextField):
#     description = 'Field to save pandas objects (df or series) as serialized JSON strings'
#
#     def __init__(self, *args, **kwargs):
#         super(JSONSerializableField, self).__init__(*args, **kwargs)
#
#     def from_db_value(self, value, expression, connection, context):
#         return json.loads(value)
#
#     def value_to_string(self, obj):
#         return str(obj.dumps())
#
# class PandasField(models.TextField):
#     description = 'Field to save pandas objects (df or series) as serialized JSON strings'
#
#     def __init__(self, *args, **kwargs):
#         super(PandasField, self).__init__(*args, **kwargs)
#
#     def from_db_value(self, value, expression, connection, context):
#         return pd.read_json()
#
#     def value_to_string(self, obj):
#         return str(obj.to_json())


# def init_db(db_name):
#     """
#     Initialize the database given a database file path.
#
#     Parameters
#     ----------
#     db_name : str
#         The path of the database, or name if it is in working directory
#     """
#
#     # Initialize database
#     conn = sql.connect(db_name)
#     # conn.execute("PRAGMA FOREIGN_KEYS=ON")
#     # conn.commit()
#     # conn = sql.connect(db_name)
#     # rows = conn.execute('pragma foreign_keys')
#     # for row in rows:
#     #     print('pragma')
#     #     print(row)
#
#     c = conn.cursor()
#
#     c.execute("""\
#        CREATE TABLE IF NOT EXISTS experimentTable
#        (experiment_id INTEGER PRIMARY KEY, import_date TEXT, experiment_title TEXT,
#        experiment_start_date TEXT, experiment_end_date TEXT, primary_scientist_name TEXT,
#        secondary_scientist_name TEXT, medium_base TEXT, medium_supplements TEXT, notes TEXT)
#     """)
#
#
#     c.execute("""\
#        CREATE TABLE IF NOT EXISTS replicateTable
#          (replicateID INTEGER PRIMARY KEY, experiment_id INT,
#           strain_id TEXT, id_1 TEXT, id_2 TEXT, id_3 TEXT,
#           FOREIGN KEY(experiment_id) REFERENCES experimentTable(experiment_id) ON DELETE CASCADE)
#     """)
#
#     for suffix in ['', '_avg', '_std']:
#         c.execute("""\
#            CREATE TABLE IF NOT EXISTS singleTrialTable""" + suffix + """
#            (singleTrialID""" + suffix + """ INTEGER PRIMARY KEY, replicateID INT, replicate_id INT, yieldsDict BLOB,
#            FOREIGN KEY(replicateID) REFERENCES replicateTable(replicateID) ON DELETE CASCADE)
#         """)
#
#         c.execute("""\
#            CREATE TABLE IF NOT EXISTS timeCourseTable""" + suffix + """
#            (timeCourseID INTEGER PRIMARY KEY, singleTrial""" + suffix + """ID INTEGER,
#            titerType TEXT, analyte_name TEXT, time_vector BLOB, data_vector BLOB, fit_params BLOB,
#            FOREIGN KEY(singleTrial""" + suffix + """ID) REFERENCES singleTrialTable""" + suffix + """(singleTrialID""" + suffix +""") ON DELETE CASCADE)
#         """)
#
#     conn.commit()
#     c.close()
#     conn.close()