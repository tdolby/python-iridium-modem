#!/usr/bin/python3.4

import serial
import sys
import time
import logging
import threading
import re

sys.path.append('..')

from iridiummodem.modem import IridiumModem

if __name__ == '__main__':
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    modem = IridiumModem('/dev/ttyUSB0', 19200)
    modem.connect()
    print('modem.imei '+format(modem.imei))
    sys.stdout.flush()
    
    print('modem.manufacturer '+format(modem.manufacturer))
    sys.stdout.flush()
    print('modem.model '+format(modem.model))
    sys.stdout.flush()
    try:
        print('modem.supportedCommands '+format(modem.supportedCommands))
        sys.stdout.flush()
    except:
        print("supportedCommands ", sys.exc_info()[0])
        sys.stdout.flush()
        
    try:
        smsStore = modem.listStoredSms()
        print('modem.listStoredSms() '+format(smsStore))
        sys.stdout.flush()
        print('smsStore[0].number '+format(smsStore[0].number))
        sys.stdout.flush()
        print('smsStore[0].text '+format(smsStore[0].text))
        sys.stdout.flush()

    except:
        print("listStoredSms() ", sys.exc_info()[0])
        sys.stdout.flush()
        
    print('modem.signalStrength '+format(modem.signalStrength))
    sys.stdout.flush()

