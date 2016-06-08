Iridium notes
===============
*Various notes from experiments with Iridium modems*

Iridium equipment comprising a NAL Research A3LA-IG and various 9505 phones. The A3LA-IG
self-describes as a 9522, but is an earlier version than the (currently available) 9522P
and was (I think) known as a "Sebring" board.

The computers used vary from a Windows 10 PC (with a motherboard serial port) to a Raspberry
PI (original) with a Prolific pl2303 serial USB adapter.

Calls and Text messages to phones
------------
Sending messages to Iridium phones is free via [their website](https://messaging.iridium.com/)
but not all mobile phone companies will allow texts to be sent to a satellite phone; the Three
network in the U.K. appears to block calls and texts (though receiving them works as expected).
Calls from landlines work, but are expensive; Iridium have two-stage dialing to save money (call
a U.S. number and it gets routed through).

Making a data connection
------------
Once the serial connection to the computer is working, wvdial can be used to bring up a
PPP connection to the Iridium internet gateway. Details on this (and much else) can be
found at Michael Ashley's [website](http://newt.phys.unsw.edu.au/~mcba/iridiumLinux.html) but the
key part is wvdial.conf, which should look like this::

   [Modem0]
   Modem = /dev/ttyUSB0
   Baud = 19200
   SetVolume = 2
   Dial Command = ATDT
   Init1 = ATZ
   Init2 = ATS0=1V1X4E1Q0&c1
   Init3 = AT+cbst=71,0,1
   Init4 = AT+cr=1
   FlowControl = CRTSCTS
   [Dialer Defaults]
   Phone = 008816000025
   Password = none
   Username = none
   Stupid Mode = 1
   Inherits = Modem0
   New PPPD = yes

The PPP demon has to negotiate the PPP link with the gateway, and the Iridium minutes clock is
ticking the whole time; it's very much worth ensuring a high quality signal before attempting
to connect, as this makes everything go faster. See the [mailasail website](http://www.mailasail.com/Support/Iridium-Bandwidth)
for details on this.

Networking details
------------

wvdial starts pppd after dialing successfully, and IP addresses look as follows::

   --> local  IP address 192.168.11.214
   --> pppd: O[7f]
   --> remote IP address 192.168.11.254
   --> pppd: O[7f]
   --> primary   DNS address 12.127.17.72
   --> pppd: O[7f]
   --> secondary DNS address 204.97.212.10

192.168 is the standard class B for behind-firewall machines, and the nameservers are either nsX.sprintlink.net (X being 1, 2, or 3), or AT&T nameservers such as dns-rs2.bgtmo.ip.att.net.

Running curl to get an https URL shows the following an Apache access.log::
   12.47.179.48 - - [23/Apr/2016:00:16:21 +0100] "GET / HTTP/1.1" 200 271 "-" "curl/7.22.0 (x86_64-pc-linux-gnu) libcurl/7.22.0 OpenSSL/1.0.1 zlib/1.2.3.4 libidn/1.23 librtmp/2.3"

12.47.179.48 does not have a DNS name, but is owned by Iridium (provided by AT&T) according to
the whois database.

traceroute generally fails to return anything when run, but the packets are sent out and
tcpdump shows ICMP packets coming back from the various hosts with an "ICMP time exceeded in-transit"
message::

  00:32:16.671378 IP 208.25.12.250 > 192.168.11.214: ICMP time exceeded in-transit, length 36

This can be turned into a trace of addresses::

   192.168.11.254 (Iridium PPP gateway address from pppd)
   10.1.25.252
   192.168.3.254
   208.25.12.250  (no name, but "Iridium North America SPRINT-D0190C (NET-208-25-12-0-1) 208.25.12.0 - 208.25.12.255" according to whois)
   144.224.27.133 sl-gw20-phx-0-5-1-0-si208.sprintlink.net
   144.232.23.197 sl-crs1-phx-.sprintlink.net
   144.232.15.81
   144.232.7.171
   144.232.15.200
   144.232.7.171
   144.223.54.190 sl-cable27-897017-0.sprintlink.net
   195.2.30.22    xe-7-0-1-xcr1.chg.cw.net
   195.2.28.49    xe-1-1-0-xcr1.ash.cw.net
   195.2.28.41    xe-5-0-3-xcr2.ash.cw.net
   195.2.24.210   xe-8-2-3-xcr2.nyk.cw.net
   195.2.25.1     ae25-xcr1.lns.cw.net
   194.70.97.65   xe-11-2-0-16-xur1.lns.uk.cw.net
   193.195.25.69  gi6-1-0-dar3.lah.uk.cw.net
   194.159.161.89 anchor-access-4-g1-1.router.demon.net
   194.217.23.62  anchor-hg-4-g6-0-0-s2016.router.demon.net

Application usage over data network
------------
As expected, latency is the key issue across the link, but the data latency appears to be highly
variable and much greater than voice latency. Ping times on one run look as follows::

   PING 192.168.20.254 (192.168.20.254) 56(84) bytes of data.
   64 bytes from 192.168.20.254: icmp_req=1 ttl=253 time=1643 ms
   64 bytes from 192.168.20.254: icmp_req=2 ttl=253 time=3438 ms
   64 bytes from 192.168.20.254: icmp_req=3 ttl=253 time=5401 ms

and curl HTTP requests are variable as well::

   tdolby@host:/$ time curl http://x.y.z.a/
   <html><body><h1>It works!</h1></body></html>
   
   real    0m6.412s
   user    0m0.011s
   sys     0m0.000s
   tdolby@host:/$ time curl http://x.y.z.a/
   <html><body><h1>It works!</h1></body></html>
   
   real    0m19.554s
   user    0m0.007s
   sys     0m0.007s

SSL suffers significantly from this, with the back-and-forth negotiation at
the beginning causing long delays::

   --2016-05-13 23:46:48--  https://x.y.z.a/bin-small.xz
   Resolving x.y.z.a (x.y.z.a)... 1.2.3.4
   Connecting to x.y.z.a (x.y.z.a)|1.2.3.4|... connected.
   HTTP request sent, awaiting response... 200 OK
   Length: 26476 (26K)
   Saving to: ‘bin-small.xz.2’
   
        0K .......... .......... .....                           100%  335 =79s
   
   2016-05-13 23:49:22 (335 B/s) - ‘bin-small.xz.2’ saved [26476/26476]
   
   --2016-05-13 23:49:36--  https://x.y.z.a/sof.pdf
   Resolving x.y.z.a (x.y.z.a)... 1.2.3.4
   Connecting to x.y.z.a (x.y.z.a)|1.2.3.4|... connected.
   HTTP request sent, awaiting response... 200 OK
   Length: 15283 (15K) [application/pdf]
   Saving to: ‘sof.pdf’
   
        0K .......... ....                                       100%  211 =72s
   
   2016-05-13 23:51:18 (211 B/s) - ‘sof.pdf’ saved [15283/15283]

The download time itself is long, taking 70-80 seconds, but the difference between
start and end time is far greater; watching the wget command running, the main delay
is in SSL negotiation and sending the HTTP request.

UDP does not seem to suffer quite so badly, with delays of a second or two in packet
transmission but (as this is UDP) no negotiation or ack delays. In cost terms, sending
data ten times over with UDP might well be cheaper than using TCP (UDP is much faster and
so the link isn't up for as long) and just as reliable.

Output from query-modem.py for 9522
------------
Running query-modem.py (with debugging turned on) for the A3LA-IG::

   INFO: Connecting to modem on port /dev/ttyUSB0 at 19200bps
   DEBUG: write: ATZ
   DEBUG: response: ['OK']
   DEBUG: write: ATE0
   DEBUG: response: ['ATE0\r', 'OK']
   DEBUG: write: AT+CFUN?
   DEBUG: response: ['ERROR']
   DEBUG: write: AT+CMEE=1
   DEBUG: response: ['OK']
   DEBUG: write: AT+CLAC
   DEBUG: write: ATZ
   DEBUG: response: ['OK']
   DEBUG: write: ATE0
   DEBUG: response: ['ATE0\r', 'OK']
   DEBUG: write: AT&K0
   DEBUG: response: ['OK']
   DEBUG: write: AT&D0
   DEBUG: response: ['OK']
   DEBUG: write: AT+CGSN
   DEBUG: response: ['300001001651850', 'OK']
   modem.imei 300001001651850
   DEBUG: write: AT+CGMI
   DEBUG: response: ['Motorola', 'OK']
   modem.manufacturer Motorola
   DEBUG: write: AT+CGMM
   DEBUG: response: ['9522 Satellite Series', 'OK']
   modem.model 9522 Satellite Series
   DEBUG: write: AT+CLAC
   DEBUG: response: ['ERROR']
   modem.supportedCommands None
   DEBUG: write: AT+CMGL=4
   DEBUG: response: ['+CMGL:001,001,,061', '0791886126090050240E80008861269900002000614012122594002D7479D9FE96BBC86FB6380F38BFDF6776B91D4EB35DE3771B442DCFE920B3FCDD06DDCBE2799A5E06', 'OK']
   modem.listStoredSms() [<gsmmodem.modem.ReceivedSms object at 0xb6996690>]
   smsStore[0].number 008816xxxxxxxx
   smsStore[0].text x.y.z@googlemail.com Test from website
   DEBUG: write: AT+CSQ
   DEBUG: response: ['+CSQ:1', 'OK']
   modem.signalStrength 1
   
Text message reading works as expected, as do most of the other commands, but AT+CSQ returns only one value without a comma anywhere; the python-gsmmodem signalStrength() regular expressions needed to be modified to handle this.

The 9505 phones return the following::

   INFO: Connecting to modem on port /dev/ttyUSB0 at 19200bps
   DEBUG: write: ATZ
   DEBUG: response: ['OK']
   DEBUG: write: ATE0
   DEBUG: response: ['ATE0\r', 'OK']
   DEBUG: write: AT+CFUN?
   DEBUG: response: ['ERROR']
   DEBUG: write: AT+CMEE=1
   DEBUG: response: ['ERROR']
   DEBUG: write: ATZ
   DEBUG: response: ['OK']
   DEBUG: write: ATE0
   DEBUG: response: ['ATE0\r', 'OK']
   DEBUG: write: AT&K0
   DEBUG: response: ['OK']
   DEBUG: write: AT&D0
   DEBUG: response: ['OK']
   DEBUG: write: AT+CGSN
   DEBUG: response: ['300001001442120', 'OK']
   modem.imei 300001001442120
   DEBUG: write: AT+CGMI
   DEBUG: response: ['Motorola', 'OK']
   modem.manufacturer Motorola
   DEBUG: write: AT+CGMM
   DEBUG: response: ['9505 Satellite Series', 'OK']
   modem.model 9505 Satellite Series
   DEBUG: write: AT+CLAC
   DEBUG: response: ['ERROR']
   modem.supportedCommands None
   DEBUG: write: AT+CMGL=4
   DEBUG: response: ['ERROR']
   listStoredSms()  <class 'gsmmodem.exceptions.CommandError'>
   DEBUG: write: AT+CSQ
   DEBUG: response: ['+CSQ:099,099', 'OK']
   modem.signalStrength -1

In this case, AT+CSQ works in the technical sense that it returns the standard output with
a comma, but always returns 99 (as documented) regardless of any signal strength.

Misc notes from experiments
------------
2888 to query account balance

Long call setup time - 20 seconds or more, even to 2888

 *#91# for firmware version

Highly variable satellite signal strength even when the antenna is unchanged

Trying 00881662990000 as voicemail number, and 00881662900005 as SMS service gateway; messaging
works after that.


Tried out the NAL A3LA-IG using USB serial: 

stty --file=/dev/ttyUSB0  19200 cs8  -crtscts 

plus plugging in the entire assembly (power and serial) with both already connected
seemed to cause it to spring to life. Started with 

AT
OK
ATI3
SAC0307
OK

and then continued to work fine (though the serial port was set to crtscts the first time,
causing nothing to happen to begin with after the first lot of data).

A3LA-IG seems to draw a lot of RS232 current, leaving the USB serial converter unable to
transmit from the raspberry PI; receiving the initial sequence with the firmware version
worked, but nothing could be sent. Might also explain why other PCs couldn't talk to the device.

Startup current pulse on the A3LA-IG causes raspberry pi issues, and in general the PI and
the modem can't run from the same USB source without issues. Using two sources, and a USB
hub to get the serial port to have enough current, seems to do the trick, and the PI can
then dial successfully out using the modem.

9505 shows no such constraints: the RS232 interface works perfectly first time, with little
current drain; AT+CSQ? shows 99 in all cases, so detecting the signal strength (before trying
to make a call) would need to be done manually by looking at the screen.
