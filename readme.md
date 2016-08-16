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

First, clone the repository:
    
    git clone http://github.com/nvenayak/FermAT
    cd FermAT

Fresh environments can be quickly spun up using the requirements.txt

	pip install -r requirements.txt

You can install the package in two steps:

1.	For fresh installs first use: `python setup.py install` which will install dependencies, 
2.	Then, use: `python setup.py develop` which will install into your current directory.

I would install in develop mode if you plan on updating frequently. If you install it in the local directory, when you update the package contents (e.g. via git), python will use the
updated package automatically. If you install it in site-packages, you will need to run `pip setup.py install` before 
python will use the updated version (since it is stored in site-packages folder).

### FermAT_web
The development webserver can be run by executing a few commands in the FermAT_web folder:

After the first pull, a user should be created:

    python manage.py createsuperuser

Then, the server can be run and logged into by visiting http://localhost:8000 and logging in with the the newly created credentials

    python manage.py runserver

## Docker
Docker is a framework to seamlessly allow for reproducible package deployment.
A Dockerfile is included in the root directory and can be used to quickly generate an environment for the development server.

    git clone http://github.com/nvenayak/FermAT
    cd FermAT
    docker build --tag=fermat .
    docker run -p 8000:8000 fermat



Please see the relevant documentation here: http://nvenayak.github.io/FermAT/