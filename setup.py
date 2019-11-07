import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

def _requires_from_file(filename):
        return open(filename).read().splitlines()
setup(
    name='drf_allauthmail',
    version='0.1.1',
    packages=find_packages(),
    include_package_data=True,
    license='MIT License',
    description="provide endpoints of allauth's EmailAddress Model",
    long_description=README,
    url='https://github.com/fumuumuf/drf_allauthmail/',
    author='fumuumuf',
    author_email='kitosiro2@gmail.com',
    install_requires=_requires_from_file('requirements.txt'),
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.0',  
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',  
        'Programming Language :: Python :: 3.6',
    ],
)
