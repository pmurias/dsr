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
nic.set_bitrate(nic.BITRATE_28800)


#delay = 1000000 
delay =  100000 

ftype = 'a' 

print "OUR ID ",nic.get_uniq_id()
print "X:",x,'Y:',y

allohaNumber = 7 

class MAC:
    def __init__(self):
        self.nextMsg = 0
    def sendFrameRepeatedly(self,frame):
        self.sendFrame(frame)
    def sendFrame(self,frame,offset=0):
        now = max(nic.get_approx_timing(), self.nextMsg)
        for i in itertools.count(1):
            if random.randint(0, allohaNumber - 1) == 0:
#                print "sending msg after", i
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


myId = nic.get_uniq_id()

seenRequest = {}
seenReply = {}
seenMsg = {}

ack = {}

queue = Queue()

routeCache = {}

def prettyRoute(initiator, route, target, complete = False):
    return " -> ".join(map(lambda x: str(x),[initiator] + list(route) + ([] if complete else ["..."]) +  [target]))

def sendMsg(msgFrame, msgId, route, target):
    def check():
        if msgId in ack and nextHop in ack[msgId]:
             print "WE HAVE AN ACK"
        else:
             print "NO ACK FROM %d FOR %d TRYING AGAIN" % (nextHop,msgId)
             mac.sendFrame(msgFrame)
             queue.add(nic.get_approx_timing()+2000000, check)

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

def routeAndSend():
    print "REQUESTING ROUTE %d -> %d" % (myId,target)
    requestId = random.randint(0,1000)
    seenRequest[requestId] = True
    frame = MiniFrame(requestType,struct.pack(routeRequestHeader, myId, target, requestId, 0))
    mac.sendFrame(frame)
    queue.add(0, tickOnceRouted)    

def tickOnceRouted():
    if target in routeCache:
        queue.add(0, lambda: tick(0))    
    else:
        queue.add(0, tickOnceRouted)    
        

target = int(sys.argv[3]) if len(sys.argv) == 4 else None

def tick(i):
    queue.add(nic.get_approx_timing()+5 * 1000000, lambda: tick(i+1))


    msgId = random.randint(0,1000)


    packedRoute = ""
    for r in routeCache[target]:
        packedRoute += struct.pack("H",r)
    routeLen = len(routeCache[target])
    frame = MiniFrame(msgType,struct.pack(msgHeader, myId, target, msgId, routeLen)+packedRoute+"Hello World "+str(i))
    sendMsg(frame, msgId, route, target)




if target is not None:
    queue.add(0, routeAndSend)    

for i in itertools.count(1):
    data = nic.rx(deadline=0)
    if data is not None:
        frame = MiniFrame.unpack(data.bytes)
        if frame.valid:
#            print "got frame", frame.frameType
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
                    

            elif frame.frameType == replyType:
                reply = struct.unpack_from(routeReplyHeader,frame.payload)
                

                (initiator, target, replyId, routeLen) = reply

                packedRoutes = frame.payload[struct.calcsize(routeReplyHeader):]

                route = struct.unpack_from("%dH" % routeLen, packedRoutes)

                if initiator == myId:
                    print "SOURCE - FOUND ROUTE", prettyRoute(initiator, route, target, True)
                    routeCache[target] = route

                elif myId in route and replyId not in seenReply:
                    seenReply[replyId] = True
                    print "ROUTE REPLY", prettyRoute(initiator, route, target, True)
                    replyFrame = MiniFrame(replyType, frame.payload)
                    mac.sendFrameRepeatedly(replyFrame)
                else:
                    print "IGNORING REPLY", prettyRoute(initiator, route, target, True)

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
                         print "GOT MSG \033[92m"+msgPayload+"\033[0m"
                elif myId in route:
                    msgFrame = MiniFrame(msgType, frame.payload)
                    nextHop = findNextHop(route, myId)

                    if msgId not in seenMsg:
                        sendMsg(msgFrame, msgId, route, target)

                else:
                    print "IGNORING MSG",prettyRoute(initiator, route, target, True),msgPayload

                seenMsg[msgId] = True

    queue.execute(nic.get_approx_timing())



