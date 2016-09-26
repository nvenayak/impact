from .depricated import download_plot
from .jupyter import *
from .plot import *
from .input import *
from .analyze import analyze_select_replicate, analyze, delete_experiment, experimentSelect_analyze
from .export import *

import sys
import os

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.views import login, logout


from django.contrib.auth.decorators import login_required
from django.contrib.auth.signals import user_logged_in


# Add the toolbox path
sys.path.append(os.path.join(os.path.dirname(__file__),'../../'))

import impact.settings


# Set the default db_name, stored in the root directory
db_name = impact.settings.db_name   # os.path.join(os.path.dirname(__file__),"../../default_impact_db.sqlite3")


impact.init_db(db_name=db_name)

def logged_in_message(sender, user, request, **kwargs):
    """
    Add a welcome message when the user logs in
    """
    messages.info(request, "Successfully logged in as: "+request.user.username+". Welcome..")

user_logged_in.connect(logged_in_message)

# No login required
def welcome(request):
    return render(request,'impact_cloud/welcome.html')


def index(request):
    return render(request,'impact_cloud/login.html')


@login_required
def createAccount(request):
    from django.contrib.auth.models import User

    user = User.objects.create_user(request.POST['username'], request.POST['email'], request.POST['password'])
    pass

@login_required
def register(request):
    return HttpResponse('No registration page created')














