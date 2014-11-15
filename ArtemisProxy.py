import socket
from ArtemisProtocol import Decoder, Ship
import select
import argparse
from pprint import pprint

SPLITSTR = "\xef\xbe\xad\xde"

def processdata(buff):
    data = []
    workingPacket = ""
    pktIndex = 0
    while pktIndex < len(buff):
        if buff[pktIndex: pktIndex + 4] == SPLITSTR:
            if len(workingPacket) > 0:
                data.append(workingPacket)
                workingPacket = ""
            workingPacket += buff[pktIndex: pktIndex + 4]
            pktIndex += 4
        else:
            workingPacket += buff[pktIndex]
            pktIndex += 1
    return data

def connect(serverip, serverport, listenip, listenport):
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind((listenip, listenport))
    serversocket.listen(1)
    print "Waiting for connection from client on %s:%s .." % (listenip, listenport)
    #serverSock = None

    (toClientSock, addr) = serversocket.accept()
    print "got connection from ", addr

    print "conecting to artemis server at", serverip
    toServerSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    toServerSock.connect((serverip, serverport))
    print "..connected"

    return toServerSock, toClientSock

if __name__ == '__main__':
    parser = argparse.ArgumentParser("ArtemisProxy : proxy between Artemis clients and server, forwards certain events to ArtNet server")

    parser.add_argument("--serverip", type=str, help="Artemis server IP", required=True)
    parser.add_argument("--serverport", type=int, help="Artemis server port", default=2010)
    parser.add_argument("--listenip", type=str, help="ip to listen for clients on", required=True)
    parser.add_argument("--listenport", type=int, help="port to listen for clients on", default=2010)
    parser.add_argument("--artnetserverip", type=str, help="ArtNet server IP", default="")
    parser.add_argument("--sntfile", type=str, help="snt file of ship being used", required=True)

    args = parser.parse_args()

    toServerSock, toClientSock = connect(args.serverip, args.serverport, args.listenip, args.listenport)
    ship = Ship(args.sntfile)
    inputs = [toServerSock, toClientSock]

    #list of packets extracted from streams
    packets = []
    while(True):
        snd_buff = ""
        rcv_buff = ""

        (read, write, fucked) = select.select(inputs, [], [])
        packets = []
        for r in read:
            if r is toServerSock:
                #read the data from the server
                rcv_buff = toServerSock.recv(256)
            elif r is toClientSock:
                #read the data from the client
                snd_buff = toClientSock.recv(256)

            #scan the buffer for the start string and length
            packets.extend(processdata(rcv_buff))
            packets.extend(processdata(snd_buff))

        #now we've processed it we can forward data in its respective directions
        if len(rcv_buff) > 0:
            toClientSock.send(rcv_buff)
        if len(snd_buff) > 0:
            toServerSock.send(snd_buff)

        for p in packets:
            #print '## PACKET #######################'
            Pack = Decoder(ship, p)





















