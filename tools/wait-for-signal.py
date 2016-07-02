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
    parser = argparse.ArgumentParser(description='Wait for a desired signal strength (up to 15 minutes)')
    parser.add_argument('--dev', dest='dev', default='/dev/ttyUSB0',
                        help='serial device name (default: %(default)s)')
    parser.add_argument('--number', default='3',
                        help='number of successive samples required (default: %(default)s)')
    parser.add_argument('signal', help='minimum signal strength (1-5)')
    
    args = parser.parse_args()
    desiredSignal = int(args.signal)
    desiredNumber = int(args.number)
    #logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    modem = IridiumModem(args.dev, 19200)
    modem.connect()

    print('modem.model '+format(modem.model))
    sys.stdout.flush()
    
    count = 0
    successiveGoodSignals = 0
    while count < 90:
        signalStrength = int(modem.signalStrength)
        print(''+format(signalStrength), end="", flush=True)
        sys.stdout.flush()
        if signalStrength >= desiredSignal:
            successiveGoodSignals += 1
        else:
            successiveGoodSignals = 0

        if successiveGoodSignals >= desiredNumber:
            break
        time.sleep(10)
        count += 1
        
    print('')
    sys.stdout.flush()
    if successiveGoodSignals >= desiredNumber:
        print('Success')
        sys.stdout.flush()
        exit(0)
    else:
        print('Failed to acquire good signal')
        sys.stdout.flush()
        exit(-1)
