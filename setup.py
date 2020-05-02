#!/usr/bin/env python3

"""Python Iridium phone library based on python-gsmmodem
Setup script based on https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path
import sys
from distutils.cmd import Command

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

tests_require = []
test_command = [sys.executable, '-m', 'unittest', 'discover']
coverage_command = ['coverage', 'run', '-m', 'unittest', 'discover']

VERSION = 0.9

class RunUnitTests(Command):
    """ run unit tests """
    
    # Need these to keep distutils happy
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    user_options = []
    description = __doc__[1:]

    def run(self):
        import subprocess
        errno = subprocess.call(test_command)
        raise SystemExit(errno)

class RunUnitTestsCoverage(Command):
    """ run unit tests and report on code coverage using the 'coverage' tool """

    # Need these to keep distutils happy
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    user_options = []
    description = __doc__[1:]

    def run(self):
        import subprocess
        errno = subprocess.call(coverage_command)
        if errno == 0:
            subprocess.call(['coverage', 'report'])
        raise SystemExit(errno)

setup(
    name='python-iridium-modem',
    version='0.1.0',
    description='Iridium phone library',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/tdolby/python-iridium-modem',

    # Author details
    author='Trevor Dolby',
    author_email='github@tdolby.demon.co.uk',

    # Choose your license
    license='LGPLv3+',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    # What does your project relate to?
    keywords='iridium satellite phone modem',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    #packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    packages=['iridiummodem'],

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    #   py_modules=["my_module"],

    scripts=['tools/print-geolocation.py'],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['pyserial', 'python-dateutil', 'python-gsmmodem-new'],

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev,test]
    extras_require={
        'dev': ['check-manifest'],
        'test': ['coverage'],
    },
    cmdclass = {'test': RunUnitTests,
                'coverage': RunUnitTestsCoverage}
)
