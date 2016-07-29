from django import forms
from django.forms.widgets import SelectDateWidget
import datetime

class newExperimentForm(forms.Form):
    experimentTitle = forms.CharField(label='Experiment Title', initial='Toggle Switch Characterization Run 3 2016.05.13')
    principalScientistName = forms.CharField(label='Principal Scientist Name', initial='John Doe')
    notes = forms.CharField(label='notes', required=False)
    importDate = forms.DateTimeField(label='Import Date', initial=datetime.datetime.today(), disabled=True)#widget=SelectDateWidget)
    runStartDate = forms.DateField(label='Experiment Start Date', widget=SelectDateWidget, initial=datetime.date.today())
    runEndDate = forms.DateField(label='Experiment End Date', widget=SelectDateWidget, initial=datetime.date.today())
    mediumBase = forms.CharField(label='Base Medium Formulation', initial='M9')
    mediumSupplements = forms.CharField(label='Medium Supplements', initial='0.02% cAA')

class plot_options_form(forms.Form):
    use_stage_indices = forms.BooleanField(label='Use stage indices?', initial=False,required=False)
    stage_indices = forms.CharField(label='Stage Indices', required=False)
    stage = forms.IntegerField(label='Stage of Interest', required=False)
    cl_scales = forms.CharField(label='Colors', initial = "['10','qual','Paired']")
    yieldFlag = forms.BooleanField(label='Yield Flag', initial = False, required=False)
    titerFlag = forms.BooleanField(label='Titer Flag', initial = True, required=False)
    endpointFlag = forms.BooleanField(label='Endpoint Flag', initial = False, required=False)
    sortBy = forms.ChoiceField(label = 'Sort By', choices = [('strainID','strainID'),
                                                             ('identifier1','identifier1'),
                                                             ('identifier2','identifier2'),
                                                             ('None','None')])
    row_height = forms.FloatField(label = 'Row Height', initial = 300)
    column_width_multiplier = forms.FloatField(label = 'Single Panel Width', initial = 300)
    number_of_columns = forms.IntegerField(label = 'Number of columns', initial = 3)

