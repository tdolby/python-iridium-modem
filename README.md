python-iridium-modem ![travis status](https://travis-ci.org/tdolby/python-iridium-modem.svg?branch=master)
===============

*Iridium modem module for Python built on pthyon-gsmmodem*

python-iridium-modem is a module that extends the python-gsmmodem package
to enable older Iridium phones to work correctly. The standard GSM commands
expected by the base package don't always work in the assumed manner, most
especially with some AT commands used during initialisation not working as
expected. The return codes for some AT commands also produce unexpected
output in some cases (e.g., AT+CSQ). 

Testing so far includes everything from 9505 and early 9522 boards (NAL 
Research A3LA-IG) through to the 9555A, but not (yet) the 9575 or 9602.
All of these display similar characteristics, in that the phones behave as 
documented, but the python GSM module wasn't constructed to handle them.

See general [Iridium notes](docs/iridium-notes.md) for background information
and random notes from experiments.

Remove python2
Update everything!

Requirements
------------

- Python 3.4 or later
- python-gsmmodem
- pyserial
