from setuptools import setup

setup(
    name='fDAPI',
    version='0.0.0',
    packages=['fDAPI'],
    url='www.github.com/nvenayak/dataimportandplottingtoolbox',
    license='',
    author='Naveen Venayak',
    author_email='naveen.venayak@gmail.com',
    description='Toolbox for parsing, analyzing and plotting fermentation data including OD, titers and fluorescence',
    install_requires=['pyexcel_xlsx','lmfit==0.8.3','dill']
)
