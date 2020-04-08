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
commandList = { 'AT+ADJANT', 
                # +CAPBD would edit the phonebook                
                # 'AT+CAPBD', 
                'AT+CAPBR', 
                # +CAPBW would edit the phonebook . . .
                #'AT+CAPBW', 
                # +CAPPV is not intended for end users (accroding to Iridium docs)
                #'AT+CAPPV', 
                'AT+CAR?', 
                'AT+CAR=?', 
                'AT+CBC', 
                'AT+CBC=?', 
                # Set CBST to the recommend value
                'AT+CBST=71,0,1', 
                'AT+CBT', 
                'AT+CCFC=?', 
                'AT+CCLK?', 
                'AT+CCWA?', 
                'AT+CCWA=?', 
                'AT+CEER', 
                'AT+CGMI', 
                'AT+CGMM', 
                'AT+CGMR', 
                'AT+CGSN', 
                'AT+CHKIN', 
                'AT+CHLD=?', 
                'AT+CHUP', 
                'AT+CICCID', 
                'AT+CIER?', 
                'AT+CIER=?', 
                # +CKPD would press phone keys
                #'AT+CKPD=160', 
                'AT+CLCC', 
                'AT+CLCK=?', 
                # +CLIP and +CLIR do not appear to be reliably implemented and can hang
                #'AT+CLIP?', 
                #'AT+CLIR?', 
                'AT+CLVL?', 
                'AT+CLVL=?', 
                'AT+CMEE?', 
                'AT+CMEE=?', 
                # +CMGD would delete text messages
                #'AT+CMGD', 
                'AT+CMGF?', 
                'AT+CMGF=?', 
                'AT+CMGL', 
                # +CMGR would read text messages
                #'AT+CMGR', 
                # +CMGS would send text messages
                #'AT+CMGS', 
                # +CMGW would write a text messages to memory
                #'AT+CMGW', 
                'AT+CMOD?', 
                'AT+CMOD=?', 
                'AT+CMUT?', 
                'AT+CMUT=?', 
                'AT+CNMI?', 
                'AT+CNMI=?', 
                'AT+CNUM', 
                'AT+COPS?', 
                'AT+COPS=?', 
                'AT+CPAS', 
                'AT+CPBF=?', 
                'AT+CPBR=?', 
                'AT+CPBS=?', 
                'AT+CPBW=?', 
                'AT+CPIN?', 
                'AT+CPMS?', 
                'AT+CPMS=?', 
                'AT+CPWD=?', 
                'AT+CR?', 
                'AT+CR=?', 
                'AT+CRC?', 
                'AT+CRC=?', 
                'AT+CREG?', 
                'AT+CREG=?', 
                'AT+CRIS', 
                'AT+CRISX', 
                'AT+CSCA?', 
                'AT+CSCB?', 
                'AT+CSCB=?', 
                'AT+CSCS?', 
                'AT+CSCS=?', 
                'AT+CSDT?', 
                'AT+CSDT=?', 
                'AT+CSMS?', 
                'AT+CSMS=?',
                # Expect a delay for +CSQ
                'AT+CSQ', 
                'AT+CSQF', 
                'AT+CSQ=?', 
                'AT+CSQF=?', 
                # +CSSSC relies on predefined shortcodes
                #'AT+CSSSC', 
                'AT+CSTA?', 
                'AT+CSTA=?', 
                'AT+CULK?', 
                'AT+CVHU?', 
                'AT+CVHU=?', 
                'AT+CVMI', 
                # +DEBUG not sensibly testable without side-effects
                #'AT+DEBUG', 
                'AT+DR?', 
                'AT+DR=?', 
                'AT+DS?', 
                'AT+DS=?', 
                'AT+FEATURES?', 
                'AT+FWVER', 
                'AT+GCAP', 
                'AT+GEMON', 
                'AT+GMI', 
                'AT+GMM', 
                'AT+GMR', 
                'AT+GPSSTA?', 
                'AT+GPSSTA=?', 
                'AT+GPSPOS', 
                'AT+GPSUPD', 
                'AT+GSN', 
                'AT+HWVER', 
                'AT+IPR?', 
                'AT+IPR=?', 
                # +LBSECD would delete the emergency contact
                #'AT+LBSECD', 
                'AT+LBSECR=?', 
                'AT+LBSEDM=?', 
                # +LBSEMD would delete emergency messaghe recipients
                #'AT+LBSEMD', 
                'AT+LBSEMR=?', 
                'AT+LFWVER', 
                # +QGPS would send a message if recognised
                #'AT+QGPS',
                # +REBOOT would reboot the phone
                #'AT+REBOOT', 
                'AT+SBDAREG?', 
                'AT+SBDAREG=?', 
                # +SBDC would reset the MO message sequence number
                #'AT+SBDC', 
                # +SBDCC could shut the phone radio down
                #'AT+SBDCC', 
                # +SBDCR would reset PRN list for GPS
                #'AT+SBDCP', 
                # +SBDCR 
                'AT+SBDCR3', 
                # +SBDCW would clear GPS codephase data
                #'AT+SBDCW', 
                # +SBDD would delete SBD messages
                #'AT+SBDD', 
                # +SBDDET would detach from an SBD gateway
                #'AT+SBDDET', 
                'AT+SBDDSC?', 
                'AT+SBDGW', 
                'AT+SBDGWN', 
                # +SBDI[X] would start an SBD session
                #'AT+SBDI', 
                #'AT+SBDIX', 
                'AT+SBDLOE', 
                'AT+SBDMTA?', 
                'AT+SBDMTA=?', 
                'AT+SBDRB', 
                'AT+SBDREG?', 
                'AT+SBDRT', 
                'AT+SBDS', 
                'AT+SBDST?', 
                'AT+SBDSX', 
                # +SBDTC would exchange MO and MT SBD buffers
                #'AT+SBDTC', 
                # +SBDW[B,T] could overwrite an SBD message
                #'AT+SBDWB', 
                #'AT+SBDWT', 
                'AT+WANTST', 
                'AT+WDLDM?', 
                'AT+WDLDM=?', 
                'AT+WFRNG?', 
                'AT+WFRNG=?', 
                'AT+WIRLP?', 
                'AT+WIRLP=?', 
                'AT+WTM?', 
                'AT+WTM=?', 
                'AT-MSGEO', 
                'AT-MSGEOS', 
                'AT-MSSTM', 
                'AT-MSVLS?', 
                'AT-MSVLS=?', 
                'AT-MSVTR?', 
                'AT-MSVTR=?', 
                'AT-MSVTS=?',
                'ATI0',
                'ATI1',
                'ATI2',
                'ATI3',
                'ATI4',
                'ATI5',
                'ATI6',
                'ATI7',
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check command support for a modem')
    parser.add_argument('--dev', dest='dev', default='/dev/ttyACM0',
                        help='serial device name (default: %(default)s)')
    args = parser.parse_args()
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    modem = IridiumModem(args.dev, 19200)
    modem.connect()

    for cmd in commandList:
        try:
            response = modem.write(cmd)
            print(''+cmd+' response '+format(response))
            sys.stdout.flush()
        except:
            pass
