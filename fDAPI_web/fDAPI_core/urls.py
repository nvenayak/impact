"""mysite URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url

import sys
sys.path.append("C:/Users/Naveen/Documents/University/Grad School/University of Toronto/Research/python/dataImportandPlottingToolbox")
from . import views

import include

urlpatterns = [
    url(r'^$',views.core),

    url(r'^registration/register$',views.register),
    url(r'^createAccount/$',views.index),

    url(r'^login/$',views.login),
    url(r'^login',views.login),

    url(r'^logout',views.logout),

    url(r'^experimentSelect/(?P<experimentID>[0-9]+)$',views.experimentSelect),
    url(r'^selectStrains/(P<identifier>[a-z|A-Z]+)/(P<identifierName>[a-z|A-Z]+)$', views.selectStrains),
    url(r'^selectStrains/$',views.selectStrains),
    url(r'^selectStrainSubset/$',views.selectStrainSubset),
    url(r'^removeStrains/$',views.removeStrains),
    url(r'^selectTiters/$',views.selectTiters),
    url(r'^clearData/$',views.clearData),


    url(r'^mainWindow/(?P<mainWindowSelection>[a-z|A-Z]+)$',views.selectMainWindow),

    url(r'^input/inputData$',views.inputData),
    url(r'^input/$',views.input),

    url(r'^newExperiment/$',views.newExperiment),
]
