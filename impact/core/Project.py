from .Experiment import Experiment
from .settings import settings
db_name = settings.db_name
# from ..database import init_db

import sqlite3 as sql

class Identifier(object):
    def __init__(self):
        self.name = ''
        self.description = ''


class Project(object):
    """
    """

    colorMap = 'Set3'

    def __init__(self):
        self.experiment_list = []

    def add_experiment(self, experiment):
        self.experiment_list.append(experiment)

    def add_user(self):
        pass

    def delete_user(self):
        pass

    def add_user_permission(self, user, permission):
        pass

    def get_experiment(self):
        pass
