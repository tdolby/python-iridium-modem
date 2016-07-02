#!/usr/bin/env python

""" Test suite for geolocation functions in iridiummodem.modem """
import sys, time, unittest, datetime, logging
sys.path.append('..')
from iridiummodem.modem import IridiumModem

class TestGeo(unittest.TestCase):
    """ Tests geolocation functions in iridiummodem.modem """

    def test_iridiumToDatetime_basic(self):
        """ Basic test for the iridiumToDatetime method """
        im = IridiumModem("/port/does/not/exist")
        dt = im.iridiumToDatetime('2c781713')
        self.assertIsInstance(dt, datetime.datetime)
        self.assertEqual(dt, datetime.datetime(2016, 6, 26, 18, 5, 30, 790000, tzinfo=datetime.timezone.utc))

    def test_iridiumToDatetime_moreValues(self):
        """ Various value tests for the iridiumToDatetime method """
        im = IridiumModem("/port/does/not/exist")
        dt = im.iridiumToDatetime('2c781714')
        self.assertEqual(dt, datetime.datetime(2016, 6, 26, 18, 5, 30, 880000, tzinfo=datetime.timezone.utc))
        dt = im.iridiumToDatetime('2c781712')
        self.assertEqual(dt, datetime.datetime(2016, 6, 26, 18, 5, 30, 700000, tzinfo=datetime.timezone.utc))
        dt = im.iridiumToDatetime('2c781702')
        self.assertEqual(dt, datetime.datetime(2016, 6, 26, 18, 5, 29, 260000, tzinfo=datetime.timezone.utc))
        dt = im.iridiumToDatetime('153456df')
        self.assertEqual(dt, datetime.datetime(2015, 5, 17, 4, 11, 23, 230000, tzinfo=datetime.timezone.utc))
        dt = im.iridiumToDatetime('2cb48ae1')
        self.assertEqual(dt, datetime.datetime(2016, 6, 30, 21, 8, 13, 330000, tzinfo=datetime.timezone.utc))

    def test_iridiumToDatetime_era0(self):
        im = IridiumModem("/port/does/not/exist")
        dt = im.iridiumToDatetime('12345678', iridiumEra=0)
        self.assertEqual(dt, datetime.datetime(1997, 4, 15, 3, 30, 1, 640000, tzinfo=datetime.timezone.utc))

    def test_iridiumToDatetime_era1(self):
        im = IridiumModem("/port/does/not/exist")
        dt = im.iridiumToDatetime('12345678', iridiumEra=1)
        self.assertEqual(dt, datetime.datetime(2008, 1, 20, 7, 20, 11, 640000, tzinfo=datetime.timezone.utc))


    def test_datetimeToIridium_basic(self):
        im = IridiumModem("/port/does/not/exist")
        dt = datetime.datetime(2016, 6, 30, 21, 38, 36, 10000, tzinfo=datetime.timezone.utc)
        it = im.datetimeToIridium(dt)
        self.assertEqual(it, int('0x2cb4d9fd', 16))

    def test_datetimeToIridium_era1(self):
        im = IridiumModem("/port/does/not/exist")
        dt = datetime.datetime(2010, 6, 30, 21, 38, 36, 120000, tzinfo=datetime.timezone.utc)
        it = im.datetimeToIridium(dt)
        self.assertEqual(it, int('0x454779E8', 16))


    def test_datetimeToIridium_era0(self):
        im = IridiumModem("/port/does/not/exist")
        dt = datetime.datetime(2006, 6, 30, 21, 38, 36, 80000, tzinfo=datetime.timezone.utc)
        it = im.datetimeToIridium(dt)
        self.assertEqual(it, int('0xd2ae1b4c', 16))


    def test_datetimeToIridiumText(self):
        im = IridiumModem("/port/does/not/exist")
        dt = datetime.datetime(2006, 6, 30, 21, 38, 36, 80000, tzinfo=datetime.timezone.utc)
        it = im.datetimeToIridium(dt)
        itHex = "%0.8x" % it
        self.assertEqual(itHex, 'd2ae1b4c')



if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    unittest.main()
