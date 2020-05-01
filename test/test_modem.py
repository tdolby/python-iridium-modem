#!/usr/bin/env python

""" Test suite for iridiummodem.modem """

from __future__ import print_function

import sys, time, unittest, logging, codecs

from datetime import datetime, timezone
import dateutil.parser
from copy import copy

from gsmmodem.exceptions import PinRequiredError, CommandError, InvalidStateException, TimeoutException,\
    CmsError, CmeError, EncodingError
from gsmmodem.modem import StatusReport, Sms, ReceivedSms

PYTHON_VERSION = sys.version_info[0]

import gsmmodem.serial_comms
import iridiummodem.modem
from iridiummodem.modem import ISUSBDStatus, SBDTransferStatus, SBDBinaryMessage
import gsmmodem.pdu
from gsmmodem.util import SimpleOffsetTzInfo

from . import fakeiridiummodems, mockserialpackage

# Silence logging exceptions
logging.raiseExceptions = False
if sys.version_info[0] == 3 and sys.version_info[1] >= 1:
    logging.getLogger('iridiummodem').addHandler(logging.NullHandler())

# The fake modem to use (if any)
FAKE_MODEM = None
# Write callback to use during Serial.__init__() - usually None, but useful for setting write callbacks during modem.connect()
SERIAL_WRITE_CALLBACK_FUNC = None


class TestIridiumModemGeneralApi(unittest.TestCase):
    """ Tests the API of iridiummodem class (excluding connect/close) """
    
    def setUp(self):
        # Override the pyserial import        
        self.mockSerial = mockserialpackage.MockSerialPackage()
        iridiummodem.modem.IridiumModem.useWrapperSerial = False # Stop the modem class from overwriting mockSerial
        gsmmodem.serial_comms.serial = self.mockSerial
        self.modem = iridiummodem.modem.IridiumModem('-- PORT IGNORED DURING TESTS --')        
        self.modem.connect()
    
    def tearDown(self):
        self.modem.close()
        
    def test_manufacturer(self):
        def writeCallbackFunc(data):
            self.assertEqual('AT+CGMI\r', data, 'Invalid data written to modem; expected "{0}", got: "{1}"'.format('AT+CGMI\r', data))
        
        self.modem.serial.writeCallbackFunc = writeCallbackFunc
        tests = ['Iridium', 'ABCDefgh1235', 'Some Random Manufacturer']
        for test in tests:
            self.modem.serial.responseSequence = ['{0}\r\n'.format(test), 'OK\r\n']            
            self.assertEqual(test, self.modem.manufacturer)
    
        
    def test_gpsRead(self):
        # Used to check the right command is sent to the modem
        def writeCallbackFunc(data):
            self.assertEqual('AT+GPSPOS\r', data, 'Invalid data written to modem; expected "{0}", got: "{1}"'.format('AT+GPSPOS\r', data))
        
        self.modem.serial.writeCallbackFunc = writeCallbackFunc
        
        # Set fake response
        self.modem.serial.responseSequence = ['{0}\r\n'.format('00.0000,N,000.0000,E,V\r\n'), 'OK\r\n']            
        self.assertEqual([0.0, 0.0], self.modem.gpsLocation)
    
    def test_geolocation(self):
        # Used to check the right command is sent to the modem
        def writeCallbackFunc(data):
            self.assertEqual('AT-MSGEO\r', data, 'Invalid data written to modem; expected "{0}", got: "{1}"'.format('AT-MSGEO\r', data))
        
        self.modem.serial.writeCallbackFunc = writeCallbackFunc
        
        # Set fake response
        self.modem.serial.responseSequence = ['{0}\r\n'.format('-MSGEO: 4024,-96,4928,7b8bd31d\r\n'), 'OK\r\n']            
        self.assertEqual([50.758367137486,-1.366638089814213, datetime(2020, 4, 8, 17, 25, 35, 530000, tzinfo=timezone.utc)], self.modem.geoLocation)

    def test_systemtime(self):
        # Used to check the right command is sent to the modem
        def writeCallbackFunc(data):
            self.assertEqual('AT-MSSTM\r', data, 'Invalid data written to modem; expected "{0}", got: "{1}"'.format('AT-MSSTM\r', data))
        
        self.modem.serial.writeCallbackFunc = writeCallbackFunc
        
        # Set fake response
        self.modem.serial.responseSequence = ['{0}\r\n'.format('-MSSTM: 7b8bd31d\r\n'), 'OK\r\n']            
        self.assertEqual(datetime(2020, 4, 8, 17, 25, 35, 530000, tzinfo=timezone.utc), self.modem.systemTime)


    def test_sbdStatus(self):
        # Used to check the right command is sent to the modem
        def writeCallbackFunc(data):
            self.assertEqual('AT+SBDS\r', data, 'Invalid data written to modem; expected "{0}", got: "{1}"'.format('AT+SBDS\r', data))
        
        self.modem.serial.writeCallbackFunc = writeCallbackFunc
        
        # Set fake response
        self.modem.serial.responseSequence = ['{0}\r\n'.format('+SBDS: 1, 5, 0, -1\r\n'), 'OK\r\n']            
        self.assertEqual(ISUSBDStatus(5, -1, True, False, -1), self.modem.getSBDStatus)

    def test_initiateSBDSession(self):
        # Used to check the right command is sent to the modem
        def writeCallbackFunc(data):
            self.assertEqual('AT+SBDIX\r', data, 'Invalid data written to modem; expected "{0}", got: "{1}"'.format('AT+SBDIX\r', data))
        
        self.modem.serial.writeCallbackFunc = writeCallbackFunc
        
        # Set fake response
        self.modem.serial.responseSequence = ['{0}\r\n'.format('+SBDIX: 2, 6, 0, 0, 0, 0\r\n'), 'OK\r\n']
        self.assertEqual(SBDTransferStatus(6, 0, False, False, 0, 2, 0), self.modem.initiateSBDSession)

    def test_initiateOldSBDSession(self):
        # Used to check the right command is sent to the modem
        def writeCallbackFunc(data):
            self.assertEqual('AT+SBDI\r', data, 'Invalid data written to modem; expected "{0}", got: "{1}"'.format('AT+SBDI\r', data))
        
        self.modem.serial.writeCallbackFunc = writeCallbackFunc
        
        # Set fake response
        self.modem.serial.responseSequence = ['{0}\r\n'.format('+SBDI: 1, 5, 0, 0, 0, 0\r\n'), 'OK\r\n']
        self.assertEqual(SBDTransferStatus(5, 0, False, False, 0, 0, 0), self.modem.initiateOldSBDSession)

    def test_writeSBDMessageToIsu(self):
        # Set fake response
        self.modem.serial.responseSequence = ['{0}\r\n'.format('READY\r\n'), '0\r\n', 'OK\r\n','{0}\r\n'.format('+SBDS: 0, 5, 1, -1\r\n'), 'OK\r\n']

        msgToSend = SBDBinaryMessage(data=b'\x07\x08\x09\x01\x02')
        self.assertEqual(ISUSBDStatus(5, -1, False, True, -1), self.modem.writeSBDMessageToIsu(msgToSend))

    def test_readSBDMessageFromIsu(self):
        # Set fake response
        self.modem.serial.responseSequence = ['{0}\r\n'.format('+SBDS: 1, 5, 0, -1\r\n'), 'OK\r\n', '\x00\x07\x07\x08\x19\x17\x17\x12\x13\x00{\r\n', 'OK\r\n']

        self.assertEqual(SBDBinaryMessage(data=b'\x07\x08\x19\x17\x17\x12\x13'), self.modem.readSBDMessageFromIsu)


    def test_signalStrength(self):
        # Set fake response
        self.modem.serial.responseSequence = ['{0}\r\n'.format('+CSQ: 3\r\n'), 'OK\r\n']

        self.assertEqual(3, self.modem.signalStrength)

    def test_copySentSBDToReceived(self):
        # Used to check the right command is sent to the modem
        def writeCallbackFunc(data):
            self.assertEqual('AT+SBDTC\r', data, 'Invalid data written to modem; expected "{0}", got: "{1}"'.format('AT+SBDTC\r', data))
        
        self.modem.serial.writeCallbackFunc = writeCallbackFunc
        
        # Set fake response
        self.modem.serial.responseSequence = ['SBDTC: Outbound SBD Copied to Inbound SBD: size = 7\r\n', 'OK\r\n']
        # Need to fix the return value before adding assertions for the method itself
        self.modem.copySentSBDToReceived

    def test_clearIsuSBDInboundMessage(self):
        # Used to check the right command is sent to the modem
        def writeCallbackFunc(data):
            self.assertEqual('AT+SBDD1\r', data, 'Invalid data written to modem; expected "{0}", got: "{1}"'.format('AT+SBDD1\r', data))
        
        self.modem.serial.writeCallbackFunc = writeCallbackFunc
        
        # Set fake response
        self.modem.serial.responseSequence = ['0\r\n', 'OK\r\n']
        # Need to fix the return value before adding assertions for the method itself
        self.modem.clearIsuSBDInboundMessage

    def test_clearIsuSBDOutboundMessage(self):
        # Used to check the right command is sent to the modem
        def writeCallbackFunc(data):
            self.assertEqual('AT+SBDD0\r', data, 'Invalid data written to modem; expected "{0}", got: "{1}"'.format('AT+SBDD0\r', data))
        
        self.modem.serial.writeCallbackFunc = writeCallbackFunc
        
        # Set fake response
        self.modem.serial.responseSequence = ['0\r\n', 'OK\r\n']
        # Need to fix the return value before adding assertions for the method itself
        self.modem.clearIsuSBDOutboundMessage




if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    unittest.main()
