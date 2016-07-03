#!/usr/bin/python3.4

import serial
import sys
import time
import logging
import threading
import re
import argparse

sys.path.append('..')

from iridiummodem.modem import IridiumModem, SBDBinaryMessage

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send an SBD  message')
    parser.add_argument('--dev', dest='dev', default='/dev/ttyUSB0',
                        help='serial device name (default: %(default)s)')
    parser.add_argument('message', help='message to send')
    
    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    modem = IridiumModem(args.dev, 19200)
    modem.connect()

    print('modem.model '+format(modem.model))
    sys.stdout.flush()
    modem.clearIsuSBDOutboundMessage
    msgToSend = SBDBinaryMessage(data=b'hello')
    modem.writeSBDMessageToIsu(msgToSend)
    modem.getSBDStatus
    modem.clearIsuSBDInboundMessage
    modem.getSBDStatus
    modem.copySentSBDToReceived
    modem.getSBDStatus
