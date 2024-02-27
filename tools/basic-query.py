#!/usr/bin/env python

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
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    #modem = IridiumModem('/dev/ttyS0', 19200)
    #modem = IridiumModem('/dev/ttyUSB0', 19200)
    modem = IridiumModem('/dev/ttyACM0', 38400)
    modem.connect()
    try:
        print('modem.imei '+format(modem.imei))
        sys.stdout.flush() 
        print('modem.networkName '+format(modem.networkName))
        sys.stdout.flush()
    except:
        pass
    try:
        print('modem.geoLocation '+format(modem.geoLocation))
        sys.stdout.flush()
    except:
        pass
	
    try:
        print('modem.systemTime '+format(modem.systemTime))
        sys.stdout.flush()
    except:
        pass

    try:
        print('modem.testStuff '+modem.testStuff())
        sys.stdout.flush()
    except:
        pass
        
    print('modem.manufacturer '+format(modem.manufacturer))
    sys.stdout.flush()
    print('modem.model '+format(modem.model))
    sys.stdout.flush()

#    try:
#        smsStore = modem.listStoredSms()
#        print('modem.listStoredSms() '+format(smsStore))
#        sys.stdout.flush()
#        for message in (smsStore):
#            print('message: '+format(message.number)+' '+format(message.text))
#            sys.stdout.flush()
#    except:
#        print("listStoredSms() ", sys.exc_info()[0])
#        sys.stdout.flush()

    print('modem.signalStrength '+format(modem.signalStrength))
    sys.stdout.flush()

