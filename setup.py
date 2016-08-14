from setuptools import setup

setup(
    name='FermAT',
    version='0.1.0',
    packages=['FermAT'],
    url='www.github.com/nvenayak/FermAT',
    license='',
    author='Naveen Venayak',
    author_email='naveen.venayak@gmail.com',
    description='Toolbox for parsing, analyzing and plotting fermentation data including OD, titers and fluorescence',
    install_requires=['pyexcel_xlsx','lmfit==0.8.3','dill','numpy','scipy',
                      'datetime','plotly','colorlover','cobra','django','django-bootstrap-form']
)