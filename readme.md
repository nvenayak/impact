Impact: an integrated microbial physiology toolbox
==================================================
Impact is designed to help scientists parse, analyze, plot and store data for fermentation experiments.
There are two parts to the package:

## Quick Start Guide
### Install
Download a [Python 3 installation](https://www.python.org/downloads/) for your platform, 
or you can use [Anaconda](https://www.continuum.io/downloads). If you are on windows, you will need a way to install
numpy, scipy, matplotlib - packaged with Anaconda.

#### Fresh install
First, clone the repository. You will need your github username and password but if you are here presumably you are logged in.
    
    git clone http://github.com/nvenayak/impact
    cd impact

Install the dependencies for the project using requirements.txt:
	
	pip install -r requirements.txt

Install the package, use develop mode to ensure all the relative paths remain correct.

    python setup.py develop
    
#### Updating
To update to the latest version, run the following in the root folder:
    
    git pull