__author__ = 'Naveen'
from fDAPI import *
proj = Project()
exptInfo = """\
EXPERIMENT_START_DATE	2016.04.19
EXPERIMENT_END_DATE
PRINCIPAL_SCIENTIST_LAST	VENAYAK
PRINCIPAL_SCIENTIST_FIRST	NAVEEN
SECONDARY_SCIENTIST_FIRST
SECONDARY_SCIENTIST_LAST
BASE_MEDIUM	LI
SUPPLEMENTS	0.02% cAA, 2% glucose
PRECULTURE	Overnight LB, Overnight experimental medium
NOTES
"""
print(exptInfo)
# proj.newExperiment('2015.04.12','Test Description',['rawData/2016.03.30 pTOG Characterization.xlsx', 'NV_OD'])
# proj.newExperiment('2015.04.14','pTOG Test with new heat seal',['rawData/2016.04.14 pTOG Characterization.xlsx', 'NV_OD'])

# proj.newExperiment('2016.02.05','pTOG Titers Test',['rawData/2016.02.05 pTOG Characterization Titers.xlsx', 'NV_titers0.2'])

# print(proj.getExperiments())
# proj.plottingGUI()
proj.plottingGUI2()