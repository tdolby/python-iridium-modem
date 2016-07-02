#!/usr/bin/python3.4

import serial
import sys
import time
import logging
import threading
import re
import math

from datetime import datetime, timezone
import dateutil.parser


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
    _iridiumEraBases = [0, 1, 2]
    def __init__(self, port, baudrate=19200, incomingCallCallbackFunc=None, smsReceivedCallbackFunc=None, smsStatusReportCallback=None):
        super(IridiumModem, self).__init__(port, baudrate, incomingCallCallbackFunc, smsReceivedCallbackFunc, smsStatusReportCallback)
        self.timeout = 50
        self._epochBaseTime = dateutil.parser.parse("1970-01-01T00:00:00.000Z")
        self._iridiumEraBases[0] = (((dateutil.parser.parse("1996-06-01T00:00:11.000Z")) - self._epochBaseTime).total_seconds() ) * 1000
        self._iridiumEraBases[1] = (((dateutil.parser.parse("2007-03-08T03:50:21.000Z")) - self._epochBaseTime).total_seconds() ) * 1000
        self._iridiumEraBases[2] = (((dateutil.parser.parse("2014-05-11T14:23:55.000Z")) - self._epochBaseTime).total_seconds() ) * 1000

    def connect(self, pin=None):
        """ Opens the port and initializes the modem and SIM card

        :param pin: The SIM card PIN code, if any
        :type pin: str
        
        :raise PinRequiredError: if the SIM card requires a PIN but none was provided
        :raise IncorrectPinError: if the specified PIN is incorrect
        """

        # Patch the CSQ regex to work with 9522 responses
        self.CSQ_REGEX   = re.compile(r'^\+CSQ:\s*(\d+)')
        # -MSSTM: 2c6bd0b1
        self.MSSTM_REGEX = re.compile(r'^\-MSSTM:\s*([0-9A-Fa-f]+)')
        # -MSGEO: 4024,-100,4924,2c781713
        self.MSGEO_REGEX = re.compile(r'^\-MSGEO:\s*(-?\d+),(-?\d+),(-?\d+),([0-9A-Fa-f]+)')
        self.log.info('Connecting to modem on port %s at %dbps', self.port, self.baudrate)        
        self.wrapperSerial = PythonThreeFourSerialWrapper(self.port, self.baudrate, rtscts=1, timeout=50)
        try:
          super(IridiumModem, self).connect()
        except:          
          pass # This will always happen, and we ignore the exceptions and problems

        self.serial = self.wrapperSerial
        self.write('ATZ') # reset configuration
        self.write('ATE0') # echo off
        self.write('AT&K3')
        self.write('AT&D2')

    def _unlockSim(self, pin):
        if pin != None:
            super(IridiumModem, self)._unlockSim(pin)

    def _readLoop(self):
        # Intercept read loop and reassign serial
        self.serial = self.wrapperSerial
        super(IridiumModem, self)._readLoop()

    def supportedCommands(self):
        """ @return: list of AT commands supported by this modem (without the AT prefix). Returns None for Iridium modems, as they don't seem to support the AT+CLAC command  """
        return None

    def iridiumToDatetime(self, iridiumHex, iridiumEra = 2):
        """ Converts Iridium network time to a datetime object
        Useful when converting MSSTM or MSGEO(S) output.

        @raise CommandError: if an error occurs
        @param iridiumHex: Iridium time of the form 2c781713
        @param iridiumEra: Start of Iridium clock base (0=1996, 1=2007, 2=2014 (default))
        @return The GMT time as reported by the Iridium unit
        @type datetime.datetime
        """
        iridiumTime = int('0x'+(iridiumHex), 16)
        iridiumMillis = iridiumTime * 90;
        timeMillis = iridiumMillis + self._iridiumEraBases[iridiumEra]
        timeSeconds = timeMillis/1000.0
        dt = datetime.utcfromtimestamp(timeSeconds)
        # Iridium time is always UTC
        dt = dt.replace(tzinfo=timezone.utc)

        # FP conversion in datetime causes rounding errors to creep in:
        # timeSeconds: 1466973138.01 reads back as .009999
        # Trying to use round() to fix it doesn't solve the problems completely
        # in initial testing, so we take advantage of the fact we only need 
        # milliseconds (iridium time is based on 90ms ticks).
        if ( dt.microsecond % 10 ) == 9:
            dt = dt.replace(microsecond = (dt.microsecond+1))

        return dt
    

    def datetimeToIridium(self, dt):
        """ Converts a datetime object to Iridium network time

        @raise CommandError: if an error occurs
        @param dt: datetime.datetime object to convert
        @return The Iridium time representing the given datetime
        @type int 
        """
        epochSeconds = dt.timestamp(); # This is a float
        epochMilliseconds = epochSeconds * 1000

        # Assume era2 (current at time of writing) unless we end up negative
        iridiumMillis = epochMilliseconds - self._iridiumEraBases[2]
        if iridiumMillis < 0:
            iridiumMillis = epochMilliseconds - self._iridiumEraBases[1]
        if iridiumMillis < 0:
            iridiumMillis = epochMilliseconds - self._iridiumEraBases[0]
        if iridiumMillis < 0:
            # We're in trouble: the time is before the start of the Iridium network!
            raise CommandError()

        iridiumTime = int(iridiumMillis / 90)
        return iridiumTime
    
    @property
    def systemTime(self, iridiumEra = 2):
        """ Determines the current Iridium network time
        
        @raise CommandError: if an error occurs
        @param iridiumEra: Start of Iridium clock base (0=1996, 1=2007, 2=2014 (default))
        @return The current GMT time as reported by the Iridium unit
        @type datetime.datetime
        """
        response = self.write('AT-MSSTM')
        msstm = self.MSSTM_REGEX.match(response[0])
        if msstm:
            return self.iridiumToDatetime(msstm.group(1))
        else:
            raise CommandError()

    @property
    def geoLocation(self):
        response = self.write('AT-MSGEO')
        msgeo = self.MSGEO_REGEX.match(response[0])
        if msgeo:
            # -MSGEO: 4024,-100,4924,2c781713
            # lat 50.73489178019171 lon -1.423558380252216 time 2016-06-26 18:05:30.789999
            iridiumX = int(msgeo.group(1))
            iridiumY = int(msgeo.group(2))
            iridiumZ = int(msgeo.group(3))
            # From: Weisstein, Eric W. "Spherical Coordinates." From MathWorld--A Wolfram Web Resource.
            #       http://mathworld.wolfram.com/SphericalCoordinates.html 
            iridiumR = math.sqrt(math.pow(iridiumX, 2) + math.pow(iridiumY, 2) + math.pow(iridiumZ, 2))
            # Their phi is actually degrees from the north pole, so we move the base to the equator
            # by subtracting it from 90.
            lat = 90 - (math.degrees(math.acos(iridiumZ/iridiumR)))
            lon = math.degrees(math.atan(iridiumY/iridiumX))
            fixTime = self.iridiumToDatetime(msgeo.group(4))
            # print('lat '+format(lat)+' lon '+format(lon)+' time '+format(fixTime))
            return [lat, lon, fixTime]
        else:
            raise CommandError()
        
    @property
    def testStuff(self):
        #self.write('AT+SBDREG')
        self.write('AT+SBDREG?')
        #self.write('AT+SBDWT=""')
        #self.write('AT+SBDDET')
        
    
 
