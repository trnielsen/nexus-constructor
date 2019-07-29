[![License (2-Clause BSD)](https://img.shields.io/badge/license-BSD%202--Clause-blue.svg)](https://github.com/ess-dmsc/nexus-constructor/blob/master/LICENSE) [![codecov](https://codecov.io/gh/ess-dmsc/nexus-constructor/branch/master/graph/badge.svg)](https://codecov.io/gh/ess-dmsc/nexus-constructor) [![Build Status](https://jenkins.esss.dk/dm/job/ess-dmsc/job/nexus-constructor/job/master/badge/icon)](https://jenkins.esss.dk/dm/job/ess-dmsc/job/nexus-constructor/job/master/) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

# NeXus Constructor
Construct [NeXus files](https://www.nexusformat.org/) with instrument geometry information using a GUI.

![NeXus Constructor](resources/images/nc_screenshot.png)

## Installing dependencies

This project is developed for Python 3.6, so an install of 3.6 or higher
is required. https://www.python.org/downloads/

Python dependencies are listed in requirements.txt at the root of the
repository. They can be installed from a terminal by running
```
pip install -r requirements.txt
```

The black pre-commit hook (installed by [pre-commit](https://pre-commit.com/)) requires Python 3.6 or above.
You need to once run
```
pre-commit install
```
to activate the pre-commit check.

## Running the application

Run the python script `main.py` located in the root of the repository.

## Developer Documentation

See the [Wiki](wiki/Developer-Notes) for developer documentation.
