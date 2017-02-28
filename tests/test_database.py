import unittest
import impact as impt
import os

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.session = impt.create_session()
        engine = impt.bind_engine()
        impt.Base.metadata.create_all(engine)

    def tearDown(self):
        self.session.close()
        os.remove('test_impact.db')

    def test_trial_identifier(self):
        LIMS = impt.core.TrialIdentifier.Media('LIMS')
        LIMS.component_concentrations = [impt.core.TrialIdentifier.ComponentConcentration(impt.core.TrialIdentifier.MediaComponent(name), concentration, unit)
                                         for name, concentration, unit in [
                                             ['cAA', 0.02, '%'],
                                             ['IPTG', 1, 'M']
                                         ]]

        ti = impt.TrialIdentifier(strain_name='MG1655 WT')
        ti.media = LIMS
        ti.analyte_type = 'biomass'
        ti.analyte_name = 'OD600'
        strain = impt.core.TrialIdentifier.Strain(name='test strain')
        ti.strain = strain

        self.session.add(ti)
        self.session.commit()

        ti = self.session.query(impt.TrialIdentifier).all()[0]

        self.assertEqual(ti.strain.name,'test strain')
        self.trial_identifier = ti

    def test_time_course(self):
        LIMS = impt.core.TrialIdentifier.Media('LIMS')
        LIMS.component_concentrations = [impt.core.TrialIdentifier.ComponentConcentration(impt.core.TrialIdentifier.MediaComponent(name), concentration, unit)
                                         for name, concentration, unit in [
                                             ['cAA', 0.02, '%'],
                                             ['IPTG', 1, 'M']
                                         ]]

        ti = impt.TrialIdentifier(strain_name='MG1655 WT')
        ti.media = LIMS
        ti.analyte_type = 'biomass'
        ti.analyte_name = 'OD600'
        strain = impt.core.TrialIdentifier.Strain(name='test strain')
        ti.strain = strain

        self.session.add(ti)
        self.session.commit()

        ti = self.session.query(impt.TrialIdentifier).all()[0]

        tc = impt.TimeCourse()
        tc.trial_identifier = ti
        for time, data in ((0, 0), (1, 5), (2, 10)):
            tc.add_timepoint(impt.TimePoint(trial_identifier=ti, time=time, data=data))
        self.session.add(tc)
        del tc
        tc = self.session.query(impt.TimeCourse).all()[0]

        self.assertCountEqual(tc.data_vector,[0,5,10])
        self.assertCountEqual(tc.time_vector,[0,1,2])

    def test_single_trial(self):
        LIMS = impt.core.TrialIdentifier.Media('LIMS')
        LIMS.component_concentrations = [
            impt.core.TrialIdentifier.ComponentConcentration(
                impt.core.TrialIdentifier.MediaComponent(name), concentration, unit
            )
            for name, concentration, unit in [
                ['cAA', 0.02, '%'],
                ['IPTG', 1, 'M']
            ]
            ]

        ti = impt.TrialIdentifier(strain_name='MG1655 WT')
        ti.media = LIMS
        ti.analyte_type = 'biomass'
        ti.analyte_name = 'OD600'
        strain = impt.core.TrialIdentifier.Strain(name='test strain')
        ti.strain = strain

        self.session.add(ti)
        self.session.commit()

        ti = self.session.query(impt.TrialIdentifier).all()[0]

        tc = impt.TimeCourse()
        tc.trial_identifier = ti
        for time, data in ((0, 0), (1, 5), (2, 10)):
            tc.add_timepoint(impt.TimePoint(trial_identifier=ti, time=time, data=data))
        self.session.add(tc)

        st = impt.SingleTrial()
        st.add_analyte_data(tc)

        rep = impt.ReplicateTrial()
        rep.add_replicate(st)

        expt = impt.Experiment()
        expt.add_replicate_trial(rep)

        self.session.add(expt)
        self.session.commit()
        del expt

        self.session.query(impt.Experiment).all()[0]

if __name__ == 'main':
    unittest.main()