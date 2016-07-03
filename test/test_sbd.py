#!/usr/bin/env python

""" Test suite for Short Burst Data functions in iridiummodem.modem """
import sys, time, unittest, datetime, logging
sys.path.append('..')
from iridiummodem.modem import IridiumModem, SBDMessage, SBDTextMessage, SBDBinaryMessage

class TestSbd(unittest.TestCase):
    """ Tests Short Burst Data functions in iridiummodem.modem """

    def test_binary_checksum_from_Iridium_doc(self):
        """ Basic test for the SBDBinaryMessage.generateChecksum method """
        binMsg = SBDBinaryMessage(0, b'hello')
        checksum = binMsg.generateChecksum
        self.assertIsInstance(checksum, bytearray)
        self.assertEqual(2, len(checksum))
        self.assertEqual(checksum, bytearray.fromhex('0214'))

    def test_binary_checksum_overflow(self):
        """ Basic test for the SBDBinaryMessage.generateChecksum method """
        binMsg = SBDBinaryMessage(0, bytearray.fromhex('ffff'))
        checksum = binMsg.generateChecksum
        self.assertIsInstance(checksum, bytearray)
        self.assertEqual(2, len(checksum))
        self.assertEqual(checksum, bytearray.fromhex('01fe'))

    def test_binary_checksum_long(self):
        """ Basic test for the SBDBinaryMessage.generateChecksum method """
        binMsg = SBDBinaryMessage(0, bytearray.fromhex('ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00ff00'))
        checksum = binMsg.generateChecksum
        self.assertIsInstance(checksum, bytearray)
        self.assertEqual(2, len(checksum))
        self.assertEqual(checksum, bytearray.fromhex('14eb'))

if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    unittest.main()
