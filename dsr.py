#!/usr/bin/python
# -*- encoding: utf-8


from dsr.miniframe import MiniFrame 
import iinic

import sys, itertools, os, struct, random

nic = iinic.NIC(iinic.NetComm())

# Zmień prędkość transmisji z domyślnej na 600 bitów na sekundę
nic.set_bitrate(nic.BITRATE_600)

#Czas jest określony w mikrosekundach i będzie pilnowany

delay = 1000000 

ftype = 'a' 

print "OUR ID ",nic.get_uniq_id()

allohaNumber = 7 

class MAC:
    def sendFrame(self,frame):
        now = nic.get_approx_timing()
        for i in itertools.count(1):
            if random.randint(0, allohaNumber - 1) == 0:
                print "sending msg after", i
                nic.tx(frame.pack()).await()
                break
            else:
                nic.timing(now + delay * i)

mac = MAC()

routeRequestHeader = 'HHHB';

routeReplyHeader = routeRequestHeader

requestType = 'a'
replyType = 'b'
messageType = 'c'

discover = True

myId = nic.get_uniq_id()

seenRequest = {}
seenReply = {}

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

#                print "ROUTE REQUEST"


                request = struct.unpack_from(routeRequestHeader,frame.payload)

                (initiator, target, requestId, routeLen) = request

                packedRoutes = frame.payload[struct.calcsize(routeRequestHeader):]

                routes = struct.unpack_from("%dH" % routeLen, packedRoutes)

                #print routes


                if target == myId:
                    replyFrame = MiniFrame(replyType, frame.payload)
                    print "FOUND THE MACHINE"
                    mac.sendFrame(replyFrame)
                elif requestId not in seenRequest:
                    seenRequest[requestId] = True
                    print "PASSING THE ROUTE ON, target: ",target 
                    payload = struct.pack(routeRequestHeader, initiator, target, requestId, routeLen+1)
                    payload += packedRoutes + struct.pack('H', myId)
                    frame = MiniFrame(requestType, payload)
                    mac.sendFrame(frame)


            elif frame.frameType == replyType:
                reply = struct.unpack_from(routeReplyHeader,frame.payload)
                

                (initiator, target, replyId, routeLen) = reply

                packedRoutes = frame.payload[struct.calcsize(routeRequestHeader):]

                route = struct.unpack_from("%dH" % routeLen, packedRoutes)

                if initiator == myId:
                    print "FOUND THE ROUTE", route

                elif myId in route and replyId not in seenReply:
                    seenReply[replyId] = True
                    print "PASSING THE REPLY ON", route, ", target:", target
                    replyFrame = MiniFrame(replyType, frame.payload)
                    mac.sendFrame(replyFrame)

#                print route
                #print reply

    if len(sys.argv) == 2 and discover:
        discover = False
        target = int(sys.argv[1])

        requestId = random.randint(0,1000)

        print "REQUESTING ROUTE",myId,target



        frame = MiniFrame(requestType,struct.pack(routeRequestHeader, myId, target, requestId, 0))
        mac.sendFrame(frame)

