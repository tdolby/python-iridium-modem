#!/usr/bin/env python3

import serial
import sys

def sendCode(code):
  ser.write(bytes('AT+CLCK="CS",0,"'+format(code, '04d')+'"\r', 'utf-8'))
  line=ser.readline()
  #print(line)
  #sys.stdout.flush()
  line=ser.readline()
  #print(line)
  #sys.stdout.flush()
  textLine = line.decode("utf-8")
  if ( textLine.find("OK") != -1 ):
    return 1
  else:
    return 0

ser = serial.Serial('/dev/ttyUSB0', 19200, timeout=20, rtscts=0)
print(ser.name)

ser.write(b'ATZ\r')
line = ser.readline()
print(line)
line = ser.readline()
print(line)

for x in range(0,9999):
  #print('AT+CLCK="CS",0,"'+format(x, '04d')+'"\r')
  rc = sendCode(x)
  if ( rc == 1 ):
    print('Code '+format(x)+' succeeded')
    break;

#ser.write(b'AT+CLCK="CS",1,"1234"\r')
#line=ser.readline()
#print(line)
#line=ser.readline()
#print(line)

#line=ser.readline()
#print(line)
#line=ser.readline()
#print(line)

ser.close()
