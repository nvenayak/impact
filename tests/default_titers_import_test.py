import FermAT
import datetime
import unittest

class CoreTestCase(unittest.TestCase):
    def setUp(self):
        info = {
            'importDate': datetime.datetime.today(),
            'runStartDate': datetime.datetime.today(),
            'runEndDate':datetime.datetime.today(),
            'principalScientistName':'FermAT Test',
            'mediumBase':'NA',
            'mediumSupplements':'NA',
            'notes':'This is a test of the default_titers parser',
            'experimentTitle': 'default_titer test'
        }
        self.db_name = 'test_FermAT_db.sqlite3'

        # Create experiment
        self.expt = FermAT.Experiment(info = info)

        # Init a temp db
        FermAT.init_db(db_name=self.db_name)


    def tearDown(self):
        # Delete the temp db
        import os
        os.remove(self.db_name)


    def test_default_titers_parse(self):
        # Parse the data
        self.expt.parseRawData('default_titers', fileName='sample_input_data.xlsx')

        # Commit to the db
        experiment_id = self.expt.db_commit(db_name=self.db_name)

        # Reinstantiate and import from db
        expt = FermAT.Experiment()
        expt.db_load(db_name = self.db_name, experiment_id = experiment_id)

        # Plot
        expt.printGenericTimeCourse(titersToPlot=['pyruvate', 'acetate', '1,3-butanediol', 'acetaldehyde',
                                                  'ethanol', 'meso-2,3-butanediol', 'acetoin'],
                                    output_type='file')

    def test_default_titers_missing_data(self):
        """
        Test importing data with missing data
        """
        # Parse the data
        self.expt.parseRawData('default_titers', fileName='sample_input_data_missing_data.xlsx')

        # Commit to the db
        experiment_id = self.expt.db_commit(db_name=self.db_name)

        # Reinstantiate and import from db
        expt = FermAT.Experiment()
        expt.db_load(db_name=self.db_name, experiment_id=experiment_id)

        # Plot
        expt.printGenericTimeCourse(titersToPlot=['pyruvate', 'acetate', '1,3-butanediol', 'acetaldehyde',
                                                  'ethanol', 'meso-2,3-butanediol', 'acetoin'],
                                    output_type='file')

if __name__ == '__main__':
    unittest.main()