[![Build Status](https://travis-ci.com/nvenayak/impact.svg?token=V3Kqb5fkhiSEid1A8oyf&branch=master)](https://travis-ci.com/nvenayak/impact)

# Impact: a framework for analyzing microbial physiology

Impact assists scientists and engineers to interpret data describing microbial physiology.
Impact parses raw data from common equipment such as chromatography (HPLC), 
and plate readers. Data is automatically interpreted and built into hierarchical objects
which describe the experiments and extract features.

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