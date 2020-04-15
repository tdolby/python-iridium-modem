""" Module containing fake modem descriptors, for testing """

import abc
from copy import copy

class FakeModem(object):
    """ Abstract base class for fake modem descriptors """
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        self.responses = {}
        self.commandsNoPinRequired = []
        self.commandsSimBusy = [] # Commands that may trigger "SIM busy" errors
        self.pinLock = False
        self.defaultResponse = ['OK\r\n']
        self.pinRequiredErrorResponse = ['+CME ERROR: 11\r\n']
        self.smscNumber = None
        self.simBusyErrorCounter = 0 # Number of times to issue a "SIM busy" error
        self.deviceBusyErrorCounter = 0 # Number of times to issue a "Device busy" error
        self.cfun = 1 # +CFUN value to report back
        self.dtmfCommandBase = '+VTS='

    def getResponse(self, cmd):
        if type(cmd) == bytes:
            cmd = cmd.decode()

        if self.deviceBusyErrorCounter > 0:
            self.deviceBusyErrorCounter -= 1
            return ['+CME ERROR: 515\r\n']
        if self._pinLock and not cmd.startswith('AT+CPIN'):
            if cmd not in self.commandsNoPinRequired:
                return copy(self.pinRequiredErrorResponse)

        if cmd.startswith('AT+CPIN="'):
            self.pinLock = False
        elif self.simBusyErrorCounter > 0 and cmd in self.commandsSimBusy:
            self.simBusyErrorCounter -= 1
            return ['+CME ERROR: 14\r\n']
        if cmd == 'AT+CFUN?\r' and self.cfun != -1:
            return ['+CFUN: {0}\r\n'.format(self.cfun), 'OK\r\n']
        elif cmd == 'AT+CSCA?\r':
            if self.smscNumber != None:
                return ['+CSCA: "{0}",145\r\n'.format(self.smscNumber), 'OK\r\n']
            else:
                return ['OK\r\n']
        if cmd in self.responses:
            return copy(self.responses[cmd])
        else:
            return copy(self.defaultResponse)

    @property
    def pinLock(self):
        return self._pinLock
    @pinLock.setter
    def pinLock(self, pinLock):
        self._pinLock = pinLock
        if self._pinLock == True:
            self.responses['AT+CPIN?\r'] = ['+CPIN: SIM PIN\r\n', 'OK\r\n']
        else:
            self.responses['AT+CPIN?\r'] = ['+CPIN: READY\r\n', 'OK\r\n']

    @abc.abstractmethod
    def getAtdResponse(self, number):
        return []

    @abc.abstractmethod
    def getPreCallInitWaitSequence(self):
        return [0.1]

    @abc.abstractmethod
    def getCallInitNotification(self, callId, callType):
        return ['+WIND: 5,1\r\n', '+WIND: 2\r\n']

    @abc.abstractmethod
    def getRemoteAnsweredNotification(self, callId, callType):
        return ['OK\r\n']

    @abc.abstractmethod
    def getRemoteHangupNotification(self, callId, callType):
        return ['NO CARRIER\r\n', '+WIND: 6,1\r\n']

    def getRemoteRejectCallNotification(self, callId, callType):
        # For a lot of modems, this is the same as a hangup notification - override this if necessary!
        return self.getRemoteHangupNotification(callId, callType)

    @abc.abstractmethod
    def getIncomingCallNotification(self, callerNumber, callType='VOICE', ton=145):
        return ['RING\r\n']


class GenericTestModem(FakeModem):
    """ Not based on a real modem - simply used for general tests. Uses polling for call status updates """

    def __init__(self):
        super(GenericTestModem, self).__init__()
        self._callState = 2
        self._callNumber = None
        self._callId = None
        self.commandsNoPinRequired = ['ATZ\r', 'ATE0\r', 'AT+CFUN?\r', 'AT+CFUN=1\r', 'AT+CMEE=1\r']
        self.responses = {'AT+CPMS=?\r': ['+CPMS: ("ME","MT","SM","SR"),("ME","MT","SM","SR"),("ME","MT","SM","SR")\r\n', 'OK\r\n'],
                          'AT+CLAC=?\r': ['ERROR\r\n'],
                          'AT+CLAC\r': ['ERROR\r\n'],
                          'AT+WIND=?\r': ['ERROR\r\n'],
                          'AT+WIND?\r': ['ERROR\r\n'],
                          'AT+WIND=50\r': ['ERROR\r\n'],
                          'AT+ZPAS=?\r': ['ERROR\r\n'],
                          'AT+ZPAS?\r': ['ERROR\r\n'],
                          'AT+CSCS=?\r': ['+CSCS: ("GSM","UCS2")\r\n', 'OK\r\n'],
                          'AT+CPIN?\r': ['+CPIN: READY\r\n', 'OK\r\n'],
                          'AT\r': ['OK\r\n']}

    def getResponse(self, cmd):
        if type(cmd) == bytes:
            cmd = cmd.decode()

        if not self._pinLock and cmd == 'AT+CLCC\r':
            if self._callNumber:
                if self._callState == 0:
                    return ['+CLCC: 1,0,2,0,0,"{0}",129\r\n'.format(self._callNumber), 'OK\r\n']
                elif self._callState == 1:
                    return ['+CLCC: 1,0,0,0,0,"{0}",129\r\n'.format(self._callNumber), 'OK\r\n']
                else:
                    return ['OK\r\n']
            else:
                return super(GenericTestModem, self).getResponse(cmd)
        else:
            return super(GenericTestModem, self).getResponse(cmd)

    def getAtdResponse(self, number):
        self._callNumber = number
        self._callState = 0
        return ['OK\r\n']

    def getPreCallInitWaitSequence(self):
        return [0.1]

    def getCallInitNotification(self, callId, callType):
        return []

    def getRemoteAnsweredNotification(self, callId, callType):
        self._callState = 1
        return []

    def getRemoteHangupNotification(self, callId, callType):
        self._callState = 2
        self._callNumber = None
        return []

    def getIncomingCallNotification(self, callerNumber, callType='VOICE', ton=145):
        return ['+CRING: {0}\r\n'.format(callType), '+CLIP: "{1}",{2},,,,0\r\n'.format(callerNumber, ton)]


class Iridium9555A(GenericTestModem):
    """ Iridium satellite phone.
    """

    def __init__(self):
        super(Iridium9555A, self).__init__()
        self.responses = {'AT+CGMI\r': ['Nokia\r\n', 'OK\r\n'],
                 'AT+CGMM\r': ['Nokia N79\r\n', 'OK\r\n'],
                 'AT+CGMR\r': ['V ICPR72_08w44.1\r\n', '24-11-08\r\n', 'RM-348\r\n', '(c) Nokia\r\n', '11.049\r\n', 'OK\r\n'],
                 'AT+CIMI\r': ['111111111111111\r\n', 'OK\r\n'],
                 'AT+CGSN\r': ['111111111111111\r\n', 'OK\r\n'],
                 'AT+CNMI=?\r': ['ERROR\r\n'], # SMS reading and notifications not supported
                 'AT+CNMI=2,1,0,2\r': ['ERROR\r\n'], # SMS reading and notifications not supported
                 'AT+CLAC=?\r': ['ERROR\r\n'],
                 'AT+CLAC\r': ['ERROR\r\n'],
                 'AT+WIND=?\r': ['ERROR\r\n'],
                 'AT+WIND?\r': ['ERROR\r\n'],
                 'AT+WIND=50\r': ['ERROR\r\n'],
                 'AT+ZPAS=?\r': ['ERROR\r\n'],
                 'AT+ZPAS?\r': ['ERROR\r\n'],
                 'AT+CPMS="SM","SM","SR"\r': ['ERROR\r\n'],
                 'AT+CPMS=?\r': ['+CPMS: (),(),()\r\n', 'OK\r\n'], # not supported
                 'AT+CPMS?\r': ['+CPMS: ,,,,,,,,\r\n', 'OK\r\n'], # not supported
                 'AT+CPMS=,,\r': ['ERROR\r\n'],
                 'AT+CPMS="SM","SM"\r': ['ERROR\r\n'], # not supported
                 'AT+CSMP?\r': ['+CSMP: 49,167,0,0\r\n', 'OK\r\n'],
                 'AT+GCAP\r': ['+GCAP: +CGSM,+DS,+W\r\n', 'OK\r\n'],
                 'AT+CVHU=0\r': ['OK\r\n'],
                 'AT+CPIN?\r': ['+CPIN: READY\r\n', 'OK\r\n']}
        self.commandsNoPinRequired = ['ATZ\r', 'ATE0\r', 'AT+CFUN?\r', 'AT+CFUN=1\r', 'AT+CMEE=1\r']

    def __str__(self):
        return 'Iridium 9555a'


modemClasses = [Iridium9555A]


def createModems():
    return [modem() for modem in modemClasses]
