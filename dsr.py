#!/usr/bin/python
# -*- encoding: utf-8


from dsr.miniframe import MiniFrame 
import iinic

import sys, itertools, os, struct

nic = iinic.NIC(iinic.NetComm())

# Zmień prędkość transmisji z domyślnej na 600 bitów na sekundę
nic.set_bitrate(nic.BITRATE_600)

# Tutaj określamy wiadomość, jaką będziemy wysyłali oraz co jaki czas
# chcemy ją wysyłać. Czas jest określony w mikrosekundach i będzie pilnowany
# przez timer na karcie sieciowej (co się za chwilę okaże).
#print sys.argv[1]

#msg = '0123456789ABCD01234567890'+ str(os.getpid())
msg = '01234'+ str(os.getpid())
delay = 1000000 * 3

ftype = 'a' 

print "OUR ID ",nic.get_uniq_id()

class MAC:
    def sendFrame(self,frame):
        nic.tx(frame.pack()).await()

mac = MAC()

routeRequestHeader = 'HHHB';

routeReplyHeader = routeRequestHeader

requestType = 'a'
replyType = 'b'
messageType = 'c'

discover = True

# To jest pętla od i = 1 do nieskończoności
for i in itertools.count(1):
#    print os.getpid(),"-> sending"
    # "poczekaj, aż twój zegarek będzie pokazywał wartość delay * i"
    # "wyślij wiadomość msg"
    # oraz
    # "zatrzymaj mój program dopóki wiadomość nie zostanie wysłana"


    data = nic.rx(deadline=0)
    if data is not None:
        frame = MiniFrame.unpack(data.bytes)
        if frame.valid:
            if frame.frameType == requestType:

                print "ROUTE REQUEST"


                request = struct.unpack_from(routeRequestHeader,frame.payload)

                (initiator, target, requestId, routeLen) = request

                packedRoutes = frame.payload[struct.calcsize(routeRequestHeader):]

                routes = struct.unpack_from("%dH" % routeLen, packedRoutes)

                print routes

                myId = nic.get_uniq_id()

                if target == myId:
                    replyFrame = MiniFrame(replyType, frame.payload)
                    print "STARTING A ROUTE REPLY"
                    mac.sendFrame(replyFrame)
                else: 
                    print "PASSING THE ROUTE ON"
                    payload = struct.pack(routeRequestHeader, initiator, target, requestId, routeLen+1)
                    payload += packedRoutes + struct.pack('H', myId)
                    frame = MiniFrame(requestType, payload)
                    mac.sendFrame(frame)


            elif frame.frameType == replyType:
              print "GOT A ROUTE REPLY"
              reply = struct.unpack_from(routeReplyHeader,frame.payload)
              

              (initiator, target, requestId, routeLen) = reply

              print reply

    if len(sys.argv) == 2 and discover:
        discover = False
        origin = nic.get_uniq_id()
        target = int(sys.argv[1])

        requestId = 0

        print "REQUESTING ROUTE",origin,target

        nic.timing(delay * i)


        frame = MiniFrame('a',struct.pack(routeRequestHeader, origin, target, requestId, 0))
        mac.sendFrame(frame)

