from django import forms
from django.forms.widgets import SelectDateWidget
import datetime

class newExperimentForm(forms.Form):
    importDate = forms.DateTimeField(label='Import Date', initial=datetime.datetime.today(), disabled=True)#widget=SelectDateWidget)
    runStartDate = forms.DateField(label='Experiment Start Date', widget=SelectDateWidget, initial=datetime.date.today())
    runEndDate = forms.DateField(label='Experiment End Date', widget=SelectDateWidget, initial=datetime.date.today())
    principalScientistName = forms.CharField(label='Principal Scientist Name', initial='John Doe')
    mediumBase = forms.CharField(label='Base Medium Formulation', initial='M9')
    mediumSupplements = forms.CharField(label='Medium Supplements', initial='0.02% cAA')
    notes = forms.CharField(label='notes')
    experimentTitle = forms.CharField(label='Experiment Title', initial='Toggle Switch Characterization Run 3 2016.05.13')