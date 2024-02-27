#!/usr/bin/env python3

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
    parser = argparse.ArgumentParser(description='Send an SBD message')
    parser.add_argument('--dev', dest='dev', default='/dev/ttyACM0',
                        help='serial device name (default: %(default)s)')
    parser.add_argument('message', help='message to send')
    
    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    modem = IridiumModem(args.dev, 38400)
    modem.timeout=300
    modem.connect()

    try:
        print('modem.model '+format(modem.model))
        sys.stdout.flush()
    except:
        pass
    modem.clearIsuSBDOutboundMessage
    
    #msgToSend = SBDBinaryMessage(data=b'hello')
    msgToSend = SBDBinaryMessage(data=bytearray(args.message, "utf-8"))
    
    # Binary data can be sent but not read, mostly because the gsmmodem
    # read data loop calls decode() (which defaults to utf-8) without 
    # giving us a chance to pick up the binary data itself.
    #
    # No obvious combination of PYTHONCOERCECLOCALE, PYTHONUTF8, and LC_CTYPE
    # seemed to make any difference with python 3.10 . . . 
    #msgToSend = SBDBinaryMessage(data=b'\x07\x08\xf0\x09\x10\x11')

    modem.writeSBDMessageToIsu(msgToSend)
    modem.getSBDStatus
    #modem.initiateOldSBDSession
    modem.clearIsuSBDInboundMessage
    modem.getSBDStatus
    modem.copySentSBDToReceived
    rcvMsg = modem.readSBDMessageFromIsu
    modem.clearIsuSBDInboundMessage
    print("rcvMsg |"+format(rcvMsg.data)+"|");
    #modem.testStuff
