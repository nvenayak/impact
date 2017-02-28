# coding=utf-8

"""
Custom router to separate impact_db (data) and django_db (auth, permissions, etc.)
"""

class ImpactRouter(object):
    """
    A router to control all database operations on models in the
    auth application.
    """
    def db_for_read(self, model, **hints):
        # database = getattr(model, "_DATABASE", None)
        # print('applabel ',model._meta.app_label)
        # print('db ',database)
        print('in here1')

        if model._meta.app_label in ['impact_cloud','impact']:
            print('icloud')
            return 'impact_db'
        else:
            return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label in ['impact_cloud','impact']:
            return 'impact_db'
        else:
            return None

    def allow_relation(self, obj1, obj2, **hints):
        """
         Relations between objects are allowed if both objects are
         in the master/slave pool.
         """
        db_list = ('default')
        if obj1._state.db in db_list and obj2._state.db in db_list:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        All non-auth models end up in this pool.
        """

        if db == 'impact_db':
            return app_label in ['impact_cloud','impact']
        elif app_label in ['impact_cloud','impact']:
            return db == 'impact_db'
        else:
            return None

