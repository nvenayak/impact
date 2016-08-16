FermAT: Fermentation Analysis Toolbox
=====================================
FermAT is designed to help scientists parse, analyze, plot and store data for fermentation experiments.
There are two parts to the package:

- `FermAT`: which contains the core toolbox
- `FermAT_web`: a web-based front end written in django

`FermAT_web` is designed as a wrapper for FermAT and contains most functionality. All major functionality should continue in this fashion, and be
included in the core package as much as possible.

## Quick Start Guide
### Install
Download a [link](https://www.python.org/downloads/ "Python 3 installation" for your platform, 
or you can use ` [link](https://www.continuum.io/downloads "Anaconda"). Anaconda has many of the dependencies pre-installed,
and is an easy option to get off the ground quickly. 

#### Fresh install
First, clone the repository. You will need your github username and password but if you are here presumably you are logged in.
    
    git clone http://github.com/nvenayak/FermAT
    cd FermAT

Install the dependencies for the project using requirements.txt:
	
	pip install -r requirements.txt

Install the package, if you are to be updating the package at all, I recommend

    python setup.py develop

### FermAT_web
The development webserver can be run by executing a few commands in the FermAT_web folder.
First change directory:

    cd FermAT_web

After the first pull, the database and a user should be created:

    python manage.py migrate
    python manage.py createsuperuser

Then, the server can be run and logged into by visiting http://localhost:8000 and logging in with the the newly created credentials

    python manage.py runserver

#### Updating
To update to the latest version, simply run:
    
    git pull
    
in the root folder

## Docker
Docker is a framework to seamlessly allow for reproducible package deployment.
A Dockerfile is included in the root directory and can be used to quickly generate an environment for the development server.

    git clone http://github.com/nvenayak/FermAT
    cd FermAT
    docker build --tag=fermat .
    docker run -p 8000:8000 fermat



Please see the relevant documentation here: http://nvenayak.github.io/FermAT/