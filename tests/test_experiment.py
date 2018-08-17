import unittest
import impact as impt
import os
import pandas as pd

class TestExperiment(unittest.TestCase):
    def test_add_experiment(self):
        LIMS = impt.Media('LIMS')
        components = [impt.ComponentConcentration(impt.MediaComponent(name), concentration, unit)
                           for name, concentration, unit in [
                                             ['cAA', 0.02, '%'],
                                             ['IPTG', 1, 'M']
                                         ]]
        for component in components:
            LIMS.add_component(component)
        ti1 = impt.TimeCourseIdentifier(strain=impt.Strain(name='MG1655 WT'))
        ti1.media = LIMS
        ti1.analyte_type = 'biomass'
        ti1.analyte_name = 'OD600'
        strain1 = impt.Strain(name='test strain1')
        ti1.strain = strain1
        tc1 = impt.TimeCourse()
        tc1.trial_identifier = ti1
        for time, data in ((0, 0), (1, 5), (2, 10)):
            tc1.add_timepoint(impt.TimePoint(trial_identifier=ti1, time=time, data=data))
        tc1.pd_series = pd.Series([timePoint.data for timePoint in tc1.time_points],index=[timePoint.time for timePoint in\
                                                                                         tc1.time_points])
        st1 = impt.SingleTrial()
        st1.add_analyte_data(tc1)
        rep1 = impt.ReplicateTrial()
        rep1.add_replicate(st1)
        expt1 = impt.Experiment()
        expt1.add_replicate_trial(rep1)


        LIMS = impt.Media('LIMS')
        components = [impt.ComponentConcentration(impt.MediaComponent(name), concentration, unit)
                      for name, concentration, unit in [
                          ['cAA', 0.02, '%'],
                          ['IPTG', 1, 'M']
                      ]]
        for component in components:
            LIMS.add_component(component)

        ti2 = impt.TimeCourseIdentifier(strain=impt.Strain(name='DH10B WT'))
        ti2.media = LIMS
        ti2.analyte_type = 'biomass'
        ti2.analyte_name = 'OD600'
        strain2 = impt.Strain(name='test strain2')
        ti2.strain = strain2

        tc2 = impt.TimeCourse()
        tc2.trial_identifier = ti2
        for time, data in ((0, 1), (1, 2), (2, 3)):
            tc2.add_timepoint(impt.TimePoint(trial_identifier=ti2, time=time, data=data))
        tc2.pd_series = pd.Series([timePoint.data for timePoint in tc2.time_points],
                                 index=[timePoint.time for timePoint in \
                                        tc2.time_points])

        st2 = impt.SingleTrial()
        st2.add_analyte_data(tc2)

        rep2 = impt.ReplicateTrial()
        rep2.add_replicate(st2)

        expt2 = impt.Experiment()
        expt2.add_replicate_trial(rep2)

        expt = expt1 + expt2

        expt.set_stages([(0,2)])

        self.assertCountEqual(expt.strains,['test strain1','test strain2'])
        self.assertCountEqual(expt.analyte_names,['OD600'])
        stage_tc1 = expt.stages['0-2'].replicate_trials[1].single_trials[0].analyte_dict['OD600']
        self.assertCountEqual(stage_tc1.data_vector,[1,2])
        self.assertCountEqual(stagetc1.time_vector,[0,1])
        stage_tc2 = expt.stages['0-2'].replicate_trials[0].single_trials[0].analyte_dict['OD600']
        self.assertCountEqual(stage_tc2.data_vector,[0,5])
        self.assertCountEqual(stagetc2.time_vector,[0,1])



        pass