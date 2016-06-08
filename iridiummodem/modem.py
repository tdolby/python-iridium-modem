#!/usr/bin/python3.4

import serial
import sys
import time
import logging
import threading
import re

from gsmmodem.modem import GsmModem
from serial import Serial, EIGHTBITS, PARITY_NONE, STOPBITS_ONE

class PythonThreeFourSerialWrapper(Serial):
    def __init__(self, port=None, baudrate=9600, bytesize=EIGHTBITS, parity=PARITY_NONE, stopbits=STOPBITS_ONE, timeout=None, xonxoff=False, rtscts=False, write_timeout=None, dsrdtr=False, inter_byte_timeout=None):
        super(PythonThreeFourSerialWrapper, self).__init__(port, baudrate, bytesize, parity, stopbits, timeout, xonxoff, rtscts, write_timeout, dsrdtr, inter_byte_timeout)

    def write(self, data):
        super(PythonThreeFourSerialWrapper, self).write(bytes(data, 'iso-8859-1'));

    def read(self, size=1):
        retval = super(PythonThreeFourSerialWrapper, self).read(size)
        return retval.decode('iso-8859-1')



class IridiumModem(GsmModem):
    log = logging.getLogger('gsmmodem.modem.IridiumModem')
    wrapperSerial = None

    def __init__(self, port, baudrate=19200, incomingCallCallbackFunc=None, smsReceivedCallbackFunc=None, smsStatusReportCallback=None):
        super(IridiumModem, self).__init__(port, baudrate, incomingCallCallbackFunc, smsReceivedCallbackFunc, smsStatusReportCallback)
        self.timeout = 50

    def connect(self, pin=None):
        """ Opens the port and initializes the modem and SIM card

        :param pin: The SIM card PIN code, if any
        :type pin: str
        
        :raise PinRequiredError: if the SIM card requires a PIN but none was provided
        :raise IncorrectPinError: if the specified PIN is incorrect
        """

        # Patch the CSQ regex to work with 9522 responses
        self.CSQ_REGEX = re.compile(r'^\+CSQ:\s*(\d+)')
        
        self.log.info('Connecting to modem on port %s at %dbps', self.port, self.baudrate)        
        self.wrapperSerial = PythonThreeFourSerialWrapper(self.port, self.baudrate, rtscts=0, timeout=50)
        try:
          super(IridiumModem, self).connect()
        except:          
          pass # This will always happen, and we ignore the exceptions and problems

        self.serial = self.wrapperSerial
        self.write('ATZ') # reset configuration
        self.write('ATE0') # echo off
        self.write('AT&K0')
        self.write('AT&D0')
        time.sleep(1)

    def _unlockSim(self, pin):
        if pin != None:
            super(IridiumModem, self)._unlockSim(pin)

    def _readLoop(self):
        # Intercept read loop and reassign serial
        self.serial = self.wrapperSerial
        super(IridiumModem, self)._readLoop()
