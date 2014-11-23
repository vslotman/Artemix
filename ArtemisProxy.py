import socket
from Protocol import *
import select
import argparse
from pprint import pprint
import logging
from time import time
import ArtemisIO
from bitstring import Bits

SPLITSTR = "\xef\xbe\xad\xde"

def processdata(packet, remaining=''):
    #buff = remaining + packet
    buff = packet
    data = []
    #print Bits(bytes=buff)
    workingPacket = ""
    pktIndex = 0
    while pktIndex < len(buff):
        if buff[pktIndex: pktIndex + 4] == SPLITSTR:
            if len(workingPacket) > 0:
                data.append(workingPacket)
                workingPacket = ""
            #length = ord(buff[pktIndex+4:pktIndex+8])
            #if len(buff) - pktIndex < length:
            #    # Packet didn't fit in the buffer. Try next time
            #    return data, buff[pktIndex:]
            workingPacket += buff[pktIndex: pktIndex + 4]
            pktIndex += 4
        else:
            workingPacket += buff[pktIndex]
            pktIndex += 1
    return data, ''

def connect(serverip, serverport, listenip, listenport):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.bind((listenip, listenport))
    client.listen(1)
    print "Waiting for connection from client on %s:%s .." % (listenip, listenport)
    #serverSock = None

    (toClientSock, addr) = client.accept()
    print "got connection from ", addr

    print "conecting to artemis server at", serverip
    artemis_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    artemis_server.connect((serverip, serverport))
    print "..connected"

    return artemis_server, toClientSock

if __name__ == '__main__':
    parser = argparse.ArgumentParser("ArtemisProxy : proxy between Artemis clients and server, forwards certain events to ArtNet server")

    parser.add_argument("--serverip", type=str, help="Artemis server IP", required=True)
    parser.add_argument("--serverport", type=int, help="Artemis server port", default=2010)
    parser.add_argument("--listenip", type=str, help="ip to listen for clients on", required=True)
    parser.add_argument("--listenport", type=int, help="port to listen for clients on", default=2010)
    parser.add_argument("--artnetserverip", type=str, help="ArtNet server IP", default="")
    parser.add_argument("--sntfile", type=str, help="snt file of ship being used", required=True)

    args = parser.parse_args()

    log = logging.getLogger(__name__)

    artemis_server, artemis_client = connect(args.serverip, args.serverport, args.listenip, args.listenport)

    #artemis_client = ArtemisIO.Artemis_Receiver(ip=args.listenip, port=args.listenport)
    #artemis_server = ArtemisIO.Artemis_Sender(ip=args.serverip, port=args.serverport)
    artnet_client  = ArtemisIO.ArtNet_Receiver()
    artnet_client_socket = artnet_client.get_socket()

    Senders = ArtemisIO.Sender(ArtNet_Sender={'socket': artnet_client_socket})
    #Receivers = ArtemisIO.Receiver()

    ship = Ship(args.sntfile, Senders)
    ArtemisDecoder = ArtemisDecoder(ship)

    inputs = [artemis_server, artemis_client, artnet_client_socket]

    #list of packets extracted from streams
    packets = []
    wait = time()
    rcv_remaining = ''
    snd_remaining = ''
    while 1:
        snd_buff = ""
        rcv_buff = ""

        (read, write, error) = select.select(inputs, [], [])
        packets = []
        for r in read:
            if r is artemis_server:
                #read the data from the server
                rcv_buff = artemis_server.recv(1024)
                data, rcv_remaining = processdata(rcv_buff, rcv_remaining)
                packets.extend(data)
                #print 'artemis_server' + rcv_buff + '|'
            elif r is artemis_client:
                #read the data from the client
                snd_buff = artemis_client.recv(1024)
                data, snd_remaining = processdata(snd_buff, snd_remaining)
                packets.extend(data)
            elif r is artnet_client_socket:
                print 'ArtNet data received!'
                data = artnet_client_socket.recv(2048)
                dmx = artnet_client.handle_data(data)
                #print 'toClientSock' + snd_buff + '|'
                #scan the buffer for the start string and length

            if time() > wait+5:
                wait = time()
                a = build_packet('ToggleShieldsPacket')
                snd_buff += a


            #now we've processed it we can forward data in its respective directions
            if len(rcv_buff) > 0:
                artemis_client.send(rcv_buff)
            if len(snd_buff) > 0:
                artemis_server.send(snd_buff)

            for p in packets:
                #print '## PACKET #######################'
                Pack = ArtemisDecoder.decode(p)
