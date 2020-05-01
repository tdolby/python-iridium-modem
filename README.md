python-iridium-modem ![travis status](https://travis-ci.org/tdolby/python-iridium-modem.svg?branch=master)
===============

*Iridium modem module for Python built on pthyon-gsmmodem*

python-iridium-modem is a module that extends the python-gsmmodem package
to enable older Iridium phhones to work correctly. The standard GSM commands
expected by the base package don't always work in the assumed manner, most
especially with some AT commands used during initialisation not working as
expected. The return codes for some AT commands also produce unexpected
output in some cases (e.g., AT+CSQ). 

Testing so far includes 9505 and early 9522 boards (NAL Research A3LA-IG),
which display similar characteristics. The phones behave as documented, but
the python GSM module wasn't constructed to handle them.

See general [Iridium notes](docs/iridium-notes.md) for background information
and random notes from experiments.

Note that this package overrides some pyserial interactions in python-gsmmodem
in order to allow for python 3.4 compatiblity; ideally, this code would be in
the base package.

*Merge plans*

The original author of python-gsmmodem appears to have stepped away from the
project, but it has been picked up (and renamed python-gsmmodem-new) by @babca and
is being moved forward again; this project should eventually be merged into the
new project assuming PRs are accepted.

Requirements
------------

- Python 3.4 or later
- python-gsmmodem
- pyserial


