import unittest
import impact
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

class TestParsers(unittest.TestCase):
    def test_default_HPLC_parser(self):
        expt = impact.Experiment()
        expt.parse_raw_data('default_titers', fileName=os.path.join(BASE_DIR,'tests/test_data/sample_input_data.xlsx'))

        num_replicates = (len(expt.replicate_trial_dict.keys()))

        num_single_trials = len([
            single_trial_key for replicate_key in expt.replicate_trial_dict
            for single_trial_key in expt.replicate_trial_dict[replicate_key].single_trial_dict
        ])

        num_analyte_data = len([
            analyte_name for replicate_key in expt.replicate_trial_dict
            for single_trial_key in expt.replicate_trial_dict[replicate_key].single_trial_dict
            for analyte_name in expt.replicate_trial_dict[replicate_key].single_trial_dict[single_trial_key].analyte_dict
        ])

        num_time_points = len([
            time_point for replicate_key in expt.replicate_trial_dict
            for single_trial_key in expt.replicate_trial_dict[replicate_key].single_trial_dict
            for analyte_name in expt.replicate_trial_dict[replicate_key].single_trial_dict[single_trial_key].analyte_dict
            for time_point in expt.replicate_trial_dict[replicate_key].single_trial_dict[single_trial_key].analyte_dict[analyte_name].time_points
        ])

        self.assertEqual(num_replicates,7)
        self.assertEqual(num_single_trials,18)
        self.assertEqual(num_analyte_data,252)
        self.assertEqual(num_time_points,2884)

if __name__ == '__main__':
    unittest.main()