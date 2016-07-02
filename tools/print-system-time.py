#!/usr/bin/python3.4

import serial
import sys
import time
import logging
import threading
import re
import argparse

from datetime import datetime
import dateutil.parser

sys.path.append('..')

from iridiummodem.modem import IridiumModem

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start a voice call')
    parser.add_argument('--dev', dest='dev', default='/dev/ttyUSB0',
                        help='serial device name (default: %(default)s)')
    
    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    modem = IridiumModem(args.dev, 19200)
    modem.connect()

    print('modem.model '+format(modem.model))
    sys.stdout.flush()

    modem.geoLocation
    
    timeStruct = modem.systemTime
    
    timeString = time.strftime("%Y-%m-%d-%H:%M:%S", timeStruct)
    print('timeString '+format(timeString))
