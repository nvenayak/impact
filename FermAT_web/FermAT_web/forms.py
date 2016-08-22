from django import forms
from django.forms.widgets import SelectDateWidget
import datetime
import colorlover

class newExperimentForm(forms.Form):
    year_options = list(range(1950,2017))
    experiment_title = forms.CharField(label='Experiment Title', initial='Toggle Switch Characterization Run 3 2016.05.13')
    primary_scientist_name = forms.CharField(label='Principal Scientist Name', initial='John Doe')
    notes = forms.CharField(label='notes', required=False)
    import_date = forms.DateTimeField(label='Import Date', initial=datetime.datetime.today(), disabled=True)#widget=SelectDateWidget)
    experiment_start_date = forms.DateField(label='Experiment Start Date', widget=SelectDateWidget(years = year_options), initial=datetime.date.today())
    experiment_end_date = forms.DateField(label='Experiment End Date', widget=SelectDateWidget(years = year_options), initial=datetime.date.today())
    medium_base = forms.CharField(label='Base Medium Formulation', initial='M9')
    medium_supplements = forms.CharField(label='Medium Supplements', initial='0.02% cAA')

class plot_options_form(forms.Form):
    use_stage_indices = forms.BooleanField(label='Use stage indices?', initial=False,required=False)
    stage_indices = forms.CharField(label='Stage Indices',
                                    help_text='[&nbsp&nbsp[stage_start_0, stage_end_0],..,[stage_start_n, stage_end_n]&nbsp&nbsp]&nbsp&nbsp&nbsp'
                                              'E.g [[0,5],[6,10]]&nbsp&nbsp&nbsp'
                                              'Stage1: points 0 - 5    Stage2: points 6-10',
                                    required=False)
    stage = forms.IntegerField(label='Stage of Interest', required=False)
    cl_scales = forms.CharField(label='Colors', initial = "['10','qual','Paired']")
    yieldFlag = forms.BooleanField(label='Yield Flag', initial = False, required=False)
    titerFlag = forms.BooleanField(label='AnalyteData Flag', initial = True, required=False)
    endpointFlag = forms.BooleanField(label='Endpoint Flag', initial = False, required=False)
    sortBy = forms.ChoiceField(label = 'Sort By', choices = [('strain_id','strain_id'),
                                                             ('id_1','id_1'),
                                                             ('id_2','id_2'),
                                                             ('None','None')])
    row_height = forms.FloatField(label = 'Row Height', initial = 300)
    column_width_multiplier = forms.FloatField(label = 'Single Panel Width', initial = 300)
    number_of_columns = forms.IntegerField(label = 'Number of columns', initial = 3)

