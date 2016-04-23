__author__ = 'Naveen'
from fDAPI import *
proj = Project()
proj.newExperiment('2015.04.14','pTOG Test with new heat seal',['rawData/2016.04.14 pTOG Characterization.xlsx', 'NV_OD'])
proj.plottingGUI2()