import unittest
import impact as impt
import numpy as np

class TestFeatures(unittest.TestCase):
    def test_specific_productivity(self):
        ti = impt.TrialIdentifier()
        ti.analyte_name = 'OD600'
        ti.analyte_type = 'biomass'

        tc = impt.TimeCourse()
        tc.trial_identifier = ti
        tc.time_vector = [0,1,2,3,4,5]
        tc.data_vector = [0.05,0.1,0.2,0.4,0.8,1.6]

        st = impt.SingleTrial()
        st.add_analyte_data(tc)

        ti = impt.TrialIdentifier()
        ti.analyte_name = 'etoh'
        ti.analyte_type = 'product'

        tc = impt.TimeCourse()
        tc.trial_identifier = ti
        tc.time_vector = [0, 1, 2, 3, 4, 5]
        tc.data_vector = [1, 2, 3, 4, 5, 6]

        st.add_analyte_data(tc)

        self.assertCountEqual(st.analyte_dict['etoh'].specific_productivity.data,
                         np.array([20.,10.,5.,2.5,1.25,0.625]))

if __name__ == '__main__':
    unittest.main()