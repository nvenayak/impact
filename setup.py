from setuptools import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

extras = {}
for extra in ['docs','plotting','modeling']:
    with open('requirements'+'_'+extra+'.txt') as f:
        extras[extra] = f.read().splitlines()

setup(
    name='impact',
    version='0.1',
    packages=['impact'],
    url='www.github.com/nvenayak/impact',
    license='',
    author='Naveen Venayak',
    author_email='naveen.venayak@gmail.com',
    description='Framework for the analysis of microbial physiology experimental data.',
    install_requires=requirements,
    extras_require=extras
)
