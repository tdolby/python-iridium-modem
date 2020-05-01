#!/usr/bin/env python

import serial
import sys
import time
import logging
import threading
import re
import math

if sys.version_info[0] == 2:
    from datetime import datetime
else:
    from datetime import datetime, timezone
    import dateutil.parser

TERMINATOR = '\r'

from gsmmodem.modem import GsmModem
from gsmmodem.exceptions import InvalidStateException, CommandError

class bytesWrapper:
    dataBuffer = None
    def __init__(self, dataBuffer=None):
        self.dataBuffer = dataBuffer

    def encode(self):
        return self.dataBuffer

    def __add__(self, other):
        return bytesWrapper(self.dataBuffer+other)


class ISUSBDStatus(object):
    """ Status class to hold message sequence numbers and state flags """
    def __init__(self, outboundMSN=-1, inboundMSN=-1,outboundMsgPresent=False,inboundMsgPresent=False,inboundMessagesQueuedAtServer=-1):
        self.outboundMSN = outboundMSN # MOMSN
        self.inboundMSN = inboundMSN # MTMSN
        self.outboundMsgPresent = outboundMsgPresent # MO flag
        self.inboundMsgPresent =  inboundMsgPresent # MT flag
        self.inboundMessagesQueuedAtServer = inboundMessagesQueuedAtServer # MT Queued, SBDSX only

    def __eq__(self, other):
        return self.outboundMSN == other.outboundMSN and self.inboundMSN == other.inboundMSN and self.outboundMsgPresent == other.outboundMsgPresent and self.inboundMsgPresent == other.inboundMsgPresent and self.inboundMessagesQueuedAtServer == other.inboundMessagesQueuedAtServer

class SBDTransferStatus(ISUSBDStatus):
    """ Status class to hold queue length and other transfer response data """
    def __init__(self, outboundMSN=-1, inboundMSN=-1,outboundMsgPresent=False,inboundMsgPresent=False,inboundMessagesQueuedAtServer=-1,lastOutboundTransferStatus=-1,lastInboundTransferStatus=-1):
        super(SBDTransferStatus, self).__init__(outboundMSN,inboundMSN,outboundMsgPresent,inboundMsgPresent,inboundMessagesQueuedAtServer)
        self.lastOutboundTransferStatus = lastOutboundTransferStatus # MO Status
        self.lastInboundTransferStatus = lastInboundTransferStatus  # MT Status
    def __eq__(self, other):
        return super(SBDTransferStatus, self).__eq__(other) and self.lastOutboundTransferStatus == other.lastOutboundTransferStatus and self.lastInboundTransferStatus == other.lastInboundTransferStatus

class SBDMessage(object):
    """ Abstract Short Burst Data message class """

    # Sequence numbers are set by the ISU
    def __init__(self, sequence = -1):
        self.sequence = sequence

class SBDTextMessage(SBDMessage):
    """ Short Burst Data text message class """

    # Sequence numbers are set by the ISU
    def __init__(self, sequence = -1, text=''):
        super(SBDTextMessage, self).__init__(sequence)
        self.text = text

    @property
    def readMessage(self):
        return self.text



class SBDBinaryMessage(SBDMessage):
    """ Short Burst Data binary message class """

    # Sequence numbers are set by the ISU
    def __init__(self, sequence = -1, data=bytearray(b'')):
        super(SBDBinaryMessage, self).__init__(sequence)
        self.data = data

    @property
    def generateChecksum(self):
        cksum = 0
        for value in self.data:
            cksum = cksum + value
            cksum = cksum & 0x0000FFFF
        retval = bytearray(2)
        retval[0] = int(cksum/256)
        retval[1] = int(cksum - (retval[0] * 256))
        return retval

    def validateChecksum(self, checksum):
        cksum = self.generateChecksum
        if cksum != checksum:
            return False
        else:
            return True

    @property
    def readMessage(self):
        return self.data
    
    def __eq__(self, other):
        return super(SBDBinaryMessage, self).__eq__(other) and self.data == other.data




class IridiumModem(GsmModem):
    log = logging.getLogger('gsmmodem.modem.IridiumModem')
    virtualIridium = False
    _iridiumEraBases = [0, 1, 2]
    def __init__(self, port, baudrate=19200, incomingCallCallbackFunc=None, smsReceivedCallbackFunc=None, smsStatusReportCallback=None):
        super(IridiumModem, self).__init__(port, baudrate, incomingCallCallbackFunc, smsReceivedCallbackFunc, smsStatusReportCallback)
        self.timeout = 50
        if sys.version_info[0] == 2:
            self._epochBaseTime = datetime.strptime("1970-01-01T00:00:00", "%Y-%m-%dT%H:%M:%S")
            self._iridiumEraBases[0] = (((datetime.strptime("1996-06-01T00:00:11", "%Y-%m-%dT%H:%M:%S")) - self._epochBaseTime).total_seconds() ) * 1000
            self._iridiumEraBases[1] = (((datetime.strptime("2007-03-08T03:50:21", "%Y-%m-%dT%H:%M:%S")) - self._epochBaseTime).total_seconds() ) * 1000
            self._iridiumEraBases[2] = (((datetime.strptime("2014-05-11T14:23:55", "%Y-%m-%dT%H:%M:%S")) - self._epochBaseTime).total_seconds() ) * 1000
        else:
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
        # 00.0000,N,000.0000,E,V
        self.GPSPOS_REGEX = re.compile(r'^(-?\d+).(-?\d+),([A-Za-z]),(-?\d+).(-?\d+),([A-Za-z]),([0-9A-Za-z])')
        # Used for SBD write
        self.SBDWB_READY_REGEX = re.compile(r'^READY')
        self.SBDWB_RESP_REGEX = re.compile(r'^(\d+)')
        # +SBDS: 1, 5, 0, -1
        self.SBDS_REGEX = re.compile(r'^\+SBDS:\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)')
        # +SBDI: 1, 7, 0, 0, 0, 0
        self.SBDI_REGEX = re.compile(r'^\+SBDI:\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)')
        # +SBDIX: 0, 8, 0, 0, 0, 0
        self.SBDIX_REGEX = re.compile(r'^\+SBDIX:\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)')

        self.log.info('Connecting to modem on port %s at %dbps', self.port, self.baudrate)

        try:
            super(IridiumModem, self).connect()
        except InvalidStateException:
            pass # This will always happen, and we ignore the exceptions and problems

        try:
            self.write('ATZ') # reset configuration
            self.write('ATE0') # echo off
            self.write('AT&K3')
            self.write('AT&D2')
        except:
            # Might by virtual_iridium if one of the basic
            # commands returned an error; let's see if AT+GMR
            # returns "Call Processor Version: Long string"
            response = self.write('AT+GMR')
            if ': Long string' in response[0] or ': Long string' in response[1]:
                virtualIridium = True
                self.write('ATE0') # echo off
                self.SBDS_REGEX = re.compile(r'\nSBDS:\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+)')

    def _unlockSim(self, pin):
        if pin != None:
            super(IridiumModem, self)._unlockSim(pin)

    @property
    def smsEncoding(self):
        """ Set encoding for SMS inside PDU mode.

        :raise CommandError: if unable to set encoding
        :raise ValueError: if encoding is not supported by modem
        """
        return self._smsEncoding
    @smsEncoding.setter
    def smsEncoding(self, encoding):
        return

    @property
    def supportedCommands(self):
        """ @return: list of AT commands supported by this modem (without the AT prefix). Returns None for Iridium modems, as they don't seem to support the AT+CLAC command  """
        raise InvalidStateException()
        #return None

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
        iridiumMillis = iridiumTime * 90
        timeMillis = iridiumMillis + self._iridiumEraBases[iridiumEra]
        timeSeconds = timeMillis/1000.0
        dt = datetime.utcfromtimestamp(timeSeconds)
        # Iridium time is always UTC
        if sys.version_info[0] != 2:
            dt = dt.replace(tzinfo=timezone.utc)
        
        # FP conversion in datetime causes rounding errors to creep in:
        # timeSeconds: 1466973138.01 reads back as .009999
        # Trying to use round() to fix it doesn't solve the problems completely
        # in initial testing, so we take advantage of the fact we only need
        # milliseconds (iridium time is based on 90ms ticks).
        #
        # Note that this is hard to reproduce as of 20200419
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

        if sys.version_info[0] == 2:
            timeDelta = dt - self._epochBaseTime
            epochSeconds = timeDelta.total_seconds() # This is a float
            epochMilliseconds = epochSeconds * 1000
        else:
            epochSeconds = dt.timestamp() # This is a float
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
    def gpsLocation(self):
        response = self.write('AT+GPSPOS')
        gpspos = self.GPSPOS_REGEX.match(response[0])
        if gpspos:
            # 00.0000,N,000.0000,E,V
            lat = int(gpspos.group(1)) + ( int(gpspos.group(2)) / 10000 )
            lon = int(gpspos.group(4)) + ( int(gpspos.group(5)) / 10000 )
            return [lat, lon]
        else:
            raise CommandError()

    @property
    def clearIsuSBDOutboundMessage(self):
        response = self.write('AT+SBDD0')

    @property
    def clearIsuSBDInboundMessage(self):
        response = self.write('AT+SBDD1')

    @property
    def getSBDStatus(self):
        # +SBDS: 1, 5, 0, -1
        response = self.write('AT+SBDS')
        sbds = self.SBDS_REGEX.match(response[0])
        if sbds:
            ret = ISUSBDStatus()
            ret.outboundMSN = int(sbds.group(2))
            ret.inboundMSN  = int(sbds.group(4))
            if sbds.group(1) == "1":
                ret.outboundMsgPresent = True
            if sbds.group(3) == "1":
                ret.inboundMsgPresent  = True
            return ret
        else:
            raise CommandError()



    @property
    def initiateSBDSession(self):
        # +SBDIX: 0, 8, 0, 0, 0, 0
        #response = ['+SBDIX: 0, 8, 0, 0, 0, 0', 'OK']
        response = self.write('AT+SBDIX', timeout=300)
        sbdi = self.SBDIX_REGEX.match(response[0])
        if sbdi:
            ret = SBDTransferStatus()
            ret.lastOutboundTransferStatus = int(sbdi.group(1))
            ret.outboundMSN = int(sbdi.group(2))
            ret.lastInboundTransferStatus = int(sbdi.group(3))
            ret.inboundMSN  = int(sbdi.group(4))
            if int(sbdi.group(1)) > 5: # Error ocurrred during outbound transfer
                ret.outboundMsgPresent = True
            if sbdi.group(5) != "0":
                ret.inboundMsgPresent  = True
            ret.inboundMessagesQueuedAtServer = int(sbdi.group(6))
            return ret
        else:
            raise CommandError()


    @property
    def initiateOldSBDSession(self):
        # +SBDI: 1, 7, 0, 0, 0, 0
        #response = ['+SBDI: 1, 7, 0, 0, 0, 0', 'OK']
        response = self.write('AT+SBDI', timeout=300)
        sbdi = self.SBDI_REGEX.match(response[0])
        if sbdi:
            ret = SBDTransferStatus()
            # Convert to SBDIX-compatible numbers
            ret.lastOutboundTransferStatus = int(sbdi.group(1))
            if int(sbdi.group(1)) < 2:
                ret.lastOutboundTransferStatus = 0
            else:
                # Error
                ret.lastOutboundTransferStatus = 5

            ret.outboundMSN = int(sbdi.group(2))
            ret.lastInboundTransferStatus = int(sbdi.group(3))
            ret.inboundMSN  = int(sbdi.group(4))
            if sbdi.group(1) == "2": # Error ocurrred during outbound transfer
                ret.outboundMsgPresent = True
            if sbdi.group(5) != "0":
                ret.inboundMsgPresent  = True
            ret.inboundMessagesQueuedAtServer = int(sbdi.group(6))
            return ret
        else:
            raise CommandError()




    # Used for testing!
    @property
    def copySentSBDToReceived(self):
        response = self.write('AT+SBDTC')

    def writeSBDMessageToIsu(self, msg):
        response = self.write('AT+SBDWB='+format(len(msg.data)), expectedResponseTermSeq='READY')
        ready = self.SBDWB_READY_REGEX.match(response[0])
        if ready:
            messageData = msg.data + msg.generateChecksum
            #response = self.write(messageData, writeTerm=b'')
            response = self.write(bytesWrapper(messageData), writeTerm=b'')
            code = self.SBDWB_RESP_REGEX.match(response[0])
            if int(code.group(1)) == 0:
                ret = self.getSBDStatus
                msg.sequence = ret.outboundMSN
                return ret
            else:
                raise CommandError()
        else:
            raise CommandError()

    @property
    def readSBDMessageFromIsu(self):
        ret = self.getSBDStatus # Get the sequence number
        response = self.write('AT+SBDRB')
        if sys.version_info[0] == 2:
            byteResponse = bytearray(response[0], 'iso-8859-1')
        else:
            byteResponse = bytes(response[0], 'iso-8859-1')
        if len(byteResponse) < 4:
            raise CommandError()
        msgLen = int(byteResponse[0]) * 256
        msgLen = int(byteResponse[1]) + msgLen
        if len(byteResponse) != (msgLen + 2 + 2):
            raise CommandError()

        binData = byteResponse[2:(len(byteResponse)-2)]
        binMsg = SBDBinaryMessage(ret.inboundMSN, binData)
        #checksum = binMsg.generateChecksum

        cksum = byteResponse[(len(byteResponse)-2):len(byteResponse)]
        if binMsg.validateChecksum(cksum) == False:
            raise CommandError()
        return binMsg

    @property
    def testStuff(self):
        #self.write('AT+SBDREG')
        self.write('AT+SBDRT')
        #self.write('AT+SBDWT=""')
        #self.write('AT+SBDDET')

    @property
    def signalStrength(self):
        """  Checks the modem's cellular network signal strength

            Override from gsmmodem to change the timeout, as Iridium phones take
            a while to get the signal strength.

        :raise CommandError: if an error occurs

        :return: The network signal strength as an integer between 0 and 99, or -1 if it is unknown
        :rtype: int
        """

        # Should check CREG first in line with Iridium spec section 5.94
        csq = self.CSQ_REGEX.match(self.write('AT+CSQ', waitForResponse=True, timeout=60, parseError=True, writeTerm='\r', expectedResponseTermSeq=None)[0])
        if csq:
            ss = int(csq.group(1))
            return ss if ss != 99 else -1
        else:
            raise CommandError("invalid response for AT+CSQ")
    
    def write(self, data, waitForResponse=True, timeout=10, parseError=True, writeTerm=TERMINATOR, expectedResponseTermSeq=None):
        """ Write data to the modem.

        This method ad
        """
        #print('In wrapper write')
        newTimeout = timeout
        if newTimeout < 30:
            newTimeout = 30
        return super(IridiumModem, self).write(data, writeTerm=writeTerm, waitForResponse=waitForResponse, timeout=newTimeout, expectedResponseTermSeq=expectedResponseTermSeq)
