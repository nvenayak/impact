from setuptools import setup

setup(
    name='impact',
    version='0.5.0',
    packages=['impact'],
    url='www.github.com/nvenayak/impact',
    license='',
    author='Naveen Venayak',
    author_email='naveen.venayak@gmail.com',
    description='Framework for the analysis of microbial physiology experiental data.',
    install_requires=[
        'scipy>=0.17.0',
        'numpy>=1.10.4',
        'pandas',
        'lmfit==0.8.3',
        'pyexcel-xlsx>=0.1.0',

        'dill>=0.2.4',
        'Django>=1.9.5',
        'django-bootstrap-form',
        'django-bootstrap3',

        'sqlalchemy'],
    extras_require={
        'docs'              : ['sphinx_bootstrap_theme', 'nbsphinx', 'numpydoc'],
        'plotting'          : ['plotly>=1.9.10', 'colorlover', 'matplotlib>=1.5.1'],
        'metabolic_modeling': ['cobra>=0.4.1', 'cameo']}
)
