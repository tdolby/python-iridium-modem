#!/usr/bin/python3.4

import serial
import sys
import time
import logging
import threading
import re
import argparse

sys.path.append('..')

from iridiummodem.modem import IridiumModem

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send a text message')
    parser.add_argument('--dev', dest='dev', default='/dev/ttyUSB0',
                        help='serial device name (default: %(default)s)')
    parser.add_argument('number',  help='destination number for message')
    parser.add_argument('message', help='message to send')
    
    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    modem = IridiumModem(args.dev, 19200)
    modem.connect()

    print('modem.model '+format(modem.model))
    sys.stdout.flush()
    # Takes around 9 seconds to complete for a 9522A; network delivery takes another second
    sentSms = modem.sendSms(args.number, args.message, waitForDeliveryReport=False)
    # sentSms.status is always 0
    print('sentSms.status '+format(sentSms.status))
    sys.stdout.flush()
        
