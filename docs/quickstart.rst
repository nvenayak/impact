Quick Start Guide
**********************************
Download a `Python 3 installation <https://www.python.org/downloads/>`_ for your platform, 
or you can use `Anaconda <https://www.continuum.io/downloads>`_. Anaconda has many of the dependencies pre-installed,
and is an easy option to get off the ground quickly. 

Fresh environments can be quickly spun up using the requirements.txt

	pip install -r requirements.txt

It has the following dependencies:
::
    install_requires=['pyexcel_xlsx','lmfit==0.8.3','dill','numpy','scipy',
                      'datetime','plotly','colorlover','cobra','django','django-bootstrap-form']

You can install the package in two ways:

1.	'python setup.py install' which will install into your site-packages directory, 
2.	'python setup.py develop' which will install into your current directory.

I would install in develop mode if you plan on updating frequently. If you install it in the local directory, when you update the package contents (e.g. via git), python will use the
updated package automatically. If you install it in site-packages, you will need to run `pip setup.py install` before 
python will use the updated version.

Docker
*******
Docker is a framework to seamlessly allow for reproducible package deployment. 
A Dockerfile is included in the root directory and can be used to quickly generate an environment for the development server.
::
    git clone http://github.com/nvenayak/FermAT
    cd FermAT
    docker build --tag=fermat .
    docker run -p 8000:8000 fermat
