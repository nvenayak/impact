import Experiment
import ReplicateTrial
import SingleTrial
import Titer
import TrialIdentifier

__author__ = 'Naveen'
import FermAT
import FermAT.synthetic_data

# Let's generate some data using cobraPy and dFBA
import cobra
import cobra.test
import datetime

product_keys = ['EX_for_e','EX_ac_e','EX_etoh_e']

info = {
    'importDate': datetime.datetime.today(),
    'runStartDate': datetime.datetime.today(),
    'runEndDate':datetime.datetime.today(),
    'principalScientistName':'Naveen Venayak',
    'mediumBase':'NA',
    'mediumSupplements':'NA',
    'notes':'This is a test experiment input',
    'experimentTitle': '2016.05.24 PGI KO Sim'
}

n_replicates = 2

experiment = Experiment.Experiment(info = info)

for condition in ['Aerobic','Anaerobic']:
    # Let's grab the iJO1366 E. coli model
    model = cobra.test.create_test_model("ecoli")

    # Optimize the model after simulating anaerobic conditions
    if condition == 'Anaerobic':
        model.reactions.get_by_id('EX_o2_e').lower_bound = 0
        model.reactions.get_by_id('EX_o2_e').upper_bound = 0

    if condition == 'pgi_KO':
        model.reactions.get_by_id('PGI').lower_bound = 0
        model.reactions.get_by_id('PGI').upper_bound = 0

    model.optimize()
    model.summary()

    # Let's consider one substrate and four products
    biomass_keys = ['Ec_biomass_iJO1366_core_53p95M']
    substrate_keys = ['EX_glc_e']
    product_keys = ['EX_for_e','EX_ac_e','EX_etoh_e']

    import numpy as np
    y0 = [0.05, 100, 0, 0, 0]
    t = np.linspace(0,20,1000)

    replicateList = []
    for i in range(n_replicates):
        # Let's add some noise to the data to simulate experimental error and generate some more data
        dFBA_profiles = FermAT.synthetic_data.generate_data(y0, t, model, biomass_keys, substrate_keys,
                                                            product_keys, noise = 0.1, plot = False)
        replicateList.append(dFBA_profiles)

    import matplotlib.pyplot as plt
    for i, exchange in enumerate(biomass_keys+substrate_keys+product_keys):
        plt.figure(figsize=[12,6])
        for replicate in replicateList:
            plt.plot(t,replicate[exchange])
        plt.legend(['Replicate #'+repNum for repNum in ['1','2','3','4']],loc=2)
        plt.title(exchange)

    # Create the replicates by repeating the above code
    singleTrialList = []
    for replicate in replicateList:
        timeCourseList = []
        for exchange in biomass_keys+substrate_keys+product_keys:
            runIdentifier = TrialIdentifier.RunIdentifier()
            runIdentifier.strainID = 'iJO1366'
            runIdentifier.identifier1 = condition
            runIdentifier.replicate = i+1
            if exchange in biomass_keys:
                runIdentifier.titerName = exchange
                runIdentifier.titerType = 'OD'
            if exchange in substrate_keys:
                runIdentifier.titerName = exchange
                runIdentifier.titerType = 'substrate'
            if exchange in product_keys:
                runIdentifier.titerName = exchange
                runIdentifier.titerType = 'product'

            tempTimeCourse = Titer.TimeCourse()
            tempTimeCourse.runIdentifier = runIdentifier
            tempTimeCourse.timeVec = t
            tempTimeCourse.dataVec = replicate[exchange]
            timeCourseList.append(tempTimeCourse)

            # Now we can build a singleTrial object and load all the data
            singleTrial = SingleTrial.SingleTrial()
            for timeCourse in timeCourseList:
                singleTrial.add_titer(timeCourse)

        singleTrialList.append(singleTrial)

    replicateTrial = ReplicateTrial.ReplicateTrial()
    for singleTrial in singleTrialList:
        replicateTrial.add_replicate(singleTrial)


    # Finally, let's put this all into an experiment container
    experiment.add_replicate_trial(replicateTrial)


FermAT.init_db(db_name="../default_fDAPI_db.sqlite3")
# experimentID = experiment.commitToDB(dbName = "../default_fDAPI_db.sqlite3")
experiment.printGenericTimeCourse(titersToPlot = product_keys, output_type = 'file')



# plt.show()
#
# import matplotlib.pyplot as plt
# # Now let's recreate the experiment object and load the data from the db
# experiment = FermAT.Experiment()
# experiment.loadFromDB(dbName = '../default_fDAPI_db.sqlite3', experimentID = 1)
# experiment.printGenericTimeCourse(titersToPlot = product_keys, output_type = 'file')

# for key in experiment.replicateExperimentObjectDict:
#     print(vars(experiment.replicateExperimentObjectDict[key].single_trial_list[0]))
# for titersToPlot in [['OD'],product_keys]:
#     experiment.printGenericTimeCourse(titersToPlot = titersToPlot, plotCurveFit=False, removePointFraction=50)
# plt.show()
#
#
#
#
# ####### Repeat for anaerobic
