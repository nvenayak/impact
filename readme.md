Impact: an integrated microbial physiology toolbox
==================================================
Impact is designed to help scientists parse, analyze, plot and store data for fermentation experiments.
There are two parts to the package:

- `impact`: which contains the core toolbox
- `impact_cloud`: a web-based front end written in django

`impact_cloud` is designed as a wrapper for impact and contains most functionality. All major functionality should continue in this fashion, and be
included in the core package as much as possible.

## Quick Start Guide
### Install
Download a [Python 3 installation](https://www.python.org/downloads/) for your platform, or you can use [Anaconda](https://www.continuum.io/downloads). Anaconda has many of the dependencies pre-installed,
and is an easy option to get off the ground quickly. 

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
    
### impact_cloud
The development webserver can be run by executing a few commands in the impact_cloud folder.
First change directory:

    cd impact_cloud

After the first pull, the database and a user should be created:

    python manage.py migrate
    python manage.py createsuperuser

Then, the server can be run and logged into by visiting http://localhost:8000 and logging in with the the newly created credentials

    python manage.py runserver
 
## Docker
Docker is a framework to seamlessly allow for reproducible package deployment.
A Dockerfile is included in the root directory and can be used to quickly generate an environment for the development server.

    git clone http://github.com/nvenayak/impact
    cd impact
    sudo docker build --tag=impact .
    
The -v flag will ensure the database is stored on the host-machine and not the container. 
This allows persistance of the database and allows quick changes to the code and web framework to be tested.

    sudo docker run --restart=always \
                    -p 80:8000 \
                    -v ~/db:/code/db \
                    -v ~/impact/impact/impact:/code/impact \
                    -v ~/impact/impact/impact_cloud:/code/impact_cloud \
                    impact

If there is no intentions to make edits the the source code, there is no need for the second two volume flags.

    sudo docker run -d -p 80:8000 -v ~/db:/code/db impact

You can access the command line of the docker container by first getting the docker id and then attaching to it.
    
    sudo docker ps
    sudo docker exec -t -i <docker id> /bin/bash
    
You can also attach to the console using

    sudo docker attach <docker id>

Please see the relevant documentation here: http://nvenayak.github.io/impact/