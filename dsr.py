#!/usr/bin/python
# -*- encoding: utf-8


from dsr.miniframe import MiniFrame 
from dsr.queue import Queue

import iinic

import sys, itertools, os, struct, random

nic = iinic.NIC(iinic.NetComm(host='localhost'))

x = int(sys.argv[1])
y = int(sys.argv[2])

nic.set_pos(x,y)
nic.set_bitrate(nic.BITRATE_600)

#delay = 1000000 
delay =  100000 

ftype = 'a' 

print "OUR ID ",nic.get_uniq_id()
print "X:",x,'Y:',y

allohaNumber = 7 

class MAC:
    def __init__(self):
        self.nextMsg = 0
    def sendFrame(self,frame,offset=0):
        now = max(nic.get_approx_timing(), self.nextMsg)
        for i in itertools.count(1):
            if random.randint(0, allohaNumber - 1) == 0:
                print "sending msg after", i
                nic.tx(frame.pack()).await()
                break
            else:
                self.nextMsg = now + delay * i
                nic.timing(now + delay * i)

mac = MAC()

routeRequestHeader = 'HHHB';

routeReplyHeader = routeRequestHeader

msgHeader = routeRequestHeader

ackHeader = 'HH';

requestType = 'a'
replyType = 'b'
msgType = 'c'
ackType = 'k'

discover = True

myId = nic.get_uniq_id()

seenRequest = {}
seenReply = {}
seenMsg = {}

ack = {}

queue = Queue()

def prettyRoute(initiator, route, target, complete = False):
    return " -> ".join(map(lambda x: str(x),[initiator] + list(route) + ([] if complete else ["..."]) +  [target]))

def sendMsg(msgFrame, msgId, route, target):
    def check():
        if msgId in ack and nextHop in ack[msgId]:
             print "WE HAVE AN ACK"
        else:
             print "NO ACK FROM %d FOR %d TRYING AGAIN" % (nextHop,msgId)
             mac.sendFrame(msgFrame)
             queue.add(nic.get_approx_timing()+1000000, check)

    nextHop = findNextHop(route, myId)


    mac.sendFrame(msgFrame)
    queue.add(nic.get_approx_timing()+1000000, check)

def findNextHop(route,myId):
    if myId not in route:
        return route[0]
    nextHopIndex = list(route).index(myId)+1
    if nextHopIndex == len(route):
        return target
    else:
        return route[nextHopIndex]

for i in itertools.count(1):


    data = nic.rx(deadline=0)
    if data is not None:
        frame = MiniFrame.unpack(data.bytes)
        if frame.valid:
            if frame.frameType == requestType:


                request = struct.unpack_from(routeRequestHeader,frame.payload)

                (initiator, target, requestId, routeLen) = request

                packedRoutes = frame.payload[struct.calcsize(routeRequestHeader):]

                route = struct.unpack_from("%dH" % routeLen, packedRoutes)


                if target == myId:
                    replyFrame = MiniFrame(replyType, frame.payload)
                    print "TARGET - FOUND THE ROUTE", prettyRoute(initiator, route, target, True)
                    mac.sendFrame(replyFrame)
                elif requestId not in seenRequest:
                    seenRequest[requestId] = True
                    print "ADDING %d TO THE ROUTE" % myId, prettyRoute(initiator, list(route) + [myId] , target)
                    payload = struct.pack(routeRequestHeader, initiator, target, requestId, routeLen+1)
                    payload += packedRoutes + struct.pack('H', myId)
                    frame = MiniFrame(requestType, payload)
                    mac.sendFrame(frame)

            elif frame.frameType == ackType:
                (msgId, ackFrom)  = struct.unpack_from(ackHeader,frame.payload)
                
                if msgId not in ack:
                    ack[msgId] = {}

                ack[msgId][ackFrom] = True
                    
#                print "GOT ACK FROM", ackFrom

            elif frame.frameType == replyType:
                reply = struct.unpack_from(routeReplyHeader,frame.payload)
                

                (initiator, target, replyId, routeLen) = reply

                packedRoutes = frame.payload[struct.calcsize(routeReplyHeader):]

                route = struct.unpack_from("%dH" % routeLen, packedRoutes)

                if initiator == myId:
                    print "SOURCE - FOUND ROUTE", prettyRoute(initiator, route, target, True)


                    # Send a msg

                    msgId = random.randint(0,1000)


                    frame = MiniFrame(msgType,struct.pack(msgHeader, myId, target, msgId, routeLen)+packedRoutes+"Hello World")
                    sendMsg(frame, msgId, route, target)

                elif myId in route and replyId not in seenReply:
                    seenReply[replyId] = True
                    print "ROUTE REPLY", prettyRoute(initiator, route, target, True)
                    replyFrame = MiniFrame(replyType, frame.payload)
                    mac.sendFrame(replyFrame)

            elif frame.frameType == msgType:
                reply = struct.unpack_from(msgHeader,frame.payload)

                (initiator, target, msgId, routeLen) = reply
                packedRoutes = frame.payload[struct.calcsize(msgHeader):]
                route = struct.unpack_from("%dH" % routeLen, packedRoutes)

                msgPayload = frame.payload[struct.calcsize(msgHeader)+struct.calcsize("%dH" % routeLen):]

                if target == myId or myId in route:
                    print "SENDING ACK FOR %d FROM %d" % (msgId,myId)
                    ackFrame = MiniFrame(ackType, struct.pack(ackHeader, msgId, myId))
                    mac.sendFrame(ackFrame)

                if target == myId:
                    if msgId not in seenMsg:
                         print "GOT MSG",msgPayload
                elif myId in route:
                    msgFrame = MiniFrame(msgType, frame.payload)
                    nextHop = findNextHop(route, myId)

                    def check():
                        if msgId in ack and nextHop in ack[msgId]:
                             print "WE HAVE AN ACK"
                        else:
                             print "NO ACK FROM %d FOR %d TRYING AGAIN" % (nextHop,msgId)
                             mac.sendFrame(msgFrame)
                             queue.add(nic.get_approx_timing()+1000000, check)
                    if msgId not in seenMsg:
                        nextHop = findNextHop(route,myId)

                        print "next hop: %d FORWARDING MSG to " % nextHop,prettyRoute(initiator, route, target, True),msgPayload
                        mac.sendFrame(msgFrame)
                        queue.add(nic.get_approx_timing()+1000000, check)

                else:
                    print "IGNORING MSG",prettyRoute(initiator, route, target, True),msgPayload

                seenMsg[msgId] = True

    queue.execute(nic.get_approx_timing())

    if len(sys.argv) == 4 and discover:
        discover = False
        target = int(sys.argv[3])

        requestId = random.randint(0,1000)

        seenRequest[requestId] = True

        print "REQUESTING ROUTE %d -> %d" % (myId,target)



        frame = MiniFrame(requestType,struct.pack(routeRequestHeader, myId, target, requestId, 0))
        mac.sendFrame(frame)

