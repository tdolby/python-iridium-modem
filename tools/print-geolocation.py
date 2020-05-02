#!/usr/bin/env python3

import serial
import sys
import time
import logging
import threading
import re
import argparse

from datetime import datetime
import dateutil.parser

from iridiummodem.modem import IridiumModem

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Display current Iridium geolocation information')
    parser.add_argument('--dev', dest='dev', default='/dev/ttyUSB0',
                        help='serial device name (default: %(default)s)')
    parser.add_argument('-d', '--debug',  action='store_true', help='dump modem debug information (for python-iridium-modem development)')    
    
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    
    modem = IridiumModem(args.dev, 19200)
    modem.connect()

    print('modem.model '+format(modem.model))
    sys.stdout.flush()

    (lat, lon, fixTime) = modem.geoLocation

    print('lat '+format(lat)+' lon '+format(lon)+' fixTime '+format(fixTime))
