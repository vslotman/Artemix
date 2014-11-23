#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Name: luminosus ArtNet library
# Python ArtNet library to send and receive ArtNet data
# Author: Tim Henning

# Copyright 2011 Tim Henning
# Luminosus is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Luminosus is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import socket
import struct

class ArtNet_Sender():
    def __init__(self, address=(0, 0, 0), socket=False):
        self.create_lang_dict()
        self.nodes = []
        self.manually_added_nodes = []
        self.sending_method = 'unicast'
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.s.bind(("", 6454))
        self.build_header(address)
        self.ArtPoll()

    def create_lang_dict(self, language=None):
        self.lang = {}
        if language is None:
            try:
                language = application_language
            except NameError:
                language = 'English'
        if language == 'German':
            self.lang['send_ArtPoll'] = 'ArtPoll gesendet...'
            self.lang['no_nodes'] = "Es wurden keine Nodes gefuden. Zum benutzen von Unicast bitte selbst Nodes hinzufuegen"
            self.lang['one_node'] = "Ein ArtNet Node gefunden: %s"
            self.lang['multiple_nodes'] = "%s ArtNet Nodes gefunden: %s"
            self.lang['nodes_together'] = "Zusammen mit den selbsthinzugefuegten Nodes sind %s bekannt: %s"
            self.lang['unkown_sending_method'] = "Unbekannte Sendemethode"
            self.lang['closed'] = "ArtNet Sender beendet."
        elif language == 'English':
            self.lang['send_ArtPoll'] = 'Sending ArtPoll packet...'
            self.lang['no_nodes'] = "No ArtNet nodes were found. To unicast packets add nodes manually."
            self.lang['one_node'] = "Found one ArtNet Node: %s"
            self.lang['multiple_nodes'] = "Found %s ArtNet Nodes: %s"
            self.lang['nodes_together'] = "Together with the selfadded nodes, %s are known: %s"
            self.lang['unkown_sending_method'] = "Unknown sending method."
            self.lang['closed'] = "ArtNet sender closed."

    def build_header(self, address, eternity_port=1):
        header = []
        # Name, 7byte + 0x00
        header.append("Art-Net\x00")
        # OpCode ArtDMX -> 0x5000, Low Byte first
        header.append(struct.pack('<H', 0x5000))
        # Protocol Version 14, High Byte first
        header.append(struct.pack('>H', 14))
        # Order -> nope -> 0x00
        header.append("\x00")
        # Eternity Port
        header.append(chr(eternity_port))
        # Address
        net, subnet, universe = address
        header.append(struct.pack('<H', net << 8 | subnet << 4 | universe))
        self.header = "".join(header)
    
    def ArtPoll(self):
        content = []
        # Name, 7byte + 0x00
        content.append("Art-Net\x00")
        # OpCode ArtPoll -> 0x2000, Low Byte first
        content.append(struct.pack('<H', 0x2000))
        # Protocol Version 14, High Byte first
        content.append(struct.pack('>H', 14))
        # TalkToMe
        content.append(struct.pack('>H', 0b00000000))
        content.append(chr(0xe0))
        content = "".join(content)
        port = 6454
        print self.lang['send_ArtPoll']
        self.s.sendto(content, ("<broadcast>", port))
        self.nodes = []
        while True:
            try:
                self.s.settimeout(0.5)
                addr = self.s.recvfrom(2048)[1]
                if not socket.gethostname() in socket.gethostbyaddr(addr[0])[0] and addr not in self.nodes:
                    self.nodes.append(addr)
            except:
                break
        self.s.settimeout(None)
        if len(self.nodes) is 0:
            print self.lang['no_nodes']
        if len(self.nodes) is 1:
            print self.lang['one_node'] % self.nodes
        if len(self.nodes) > 1:
            print self.lang['multiple_nodes'] % (len(self.nodes), self.nodes)
        if self.manually_added_nodes != []:
            for n in self.manually_added_nodes:
                if n not in self.nodes:
                    self.nodes.append(n)
            print self.lang['nodes_together'] % (len(self.nodes), self.nodes)
        return len(self.nodes)

    def ArtDMX_unicast(self, dmxdata):
        content = [self.header]
        # Length of DMX Data, High Byte First
        content.append(struct.pack('>H', len(dmxdata)))
        # DMX Data
        content += [chr(i) for i in dmxdata]
        # stitch together
        content = "".join(content)
        # send
        for ip, port in self.nodes:
            self.s.sendto(content, (ip, port))

    def ArtDMX_broadcast(self, dmxdata):
        content = [self.header]
        # Length of DMX Data, High Byte First
        content.append(struct.pack('>H', len(dmxdata)))
        # DMX Data
        content += [chr(i) for i in dmxdata]
        # stitch together
        content = "".join(content)
        # send
        self.s.sendto(content, ('<broadcast>', 6454))

    def set_sending_method(self, method):
        if method in ('broadcast', 'unicast'):
            self.sending_method = method
            return True
        else:
            print self.lang['unkown_sending_method']
            return False

    def send_dmx_data(self, dmxdata):
        if self.sending_method == 'broadcast':
            self.ArtDMX_broadcast(dmxdata)
        else:
            self.ArtDMX_unicast(dmxdata)

    def add_artnet_node(self, node_ip):
        if node_ip not in self.nodes:
            self.manually_added_nodes.append((node_ip, 6454))
            for n in self.manually_added_nodes:
                if n not in self.nodes:
                    self.nodes.append(n)
            print self.nodes
            return True
        else:
            return False

    def set_address(self, address):
        self.build_header(address)
        return True

    def refresh_nodes(self):
        self.ArtPoll()
        return True
    
    def get_nodes(self):
        return self.nodes

    def close(self):
        self.s.close()
        print self.lang['closed']


class ArtNet_Receiver():
    def __init__(self, ip=''):
        self.create_lang_dict()
        self.universes = [[0] * 513] * 16
        self.net = 0
        self.subnet = 0
        self.ip = None
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.s.bind((ip, 6454))

    def create_lang_dict(self, language=None):
        self.lang = {}
        if language is None:
            try:
                language = application_language
            except NameError:
                language = 'English'
        if language == 'German':
            self.lang['ip_address'] = 'Bitte die IP-Adresse dieses Computers eingeben: '
            self.lang['listening_for_packets'] = 'Warte auf eingehende Pakete...'
            self.lang['invalid_id'] = "Paket mit ungueltiger ID oder Version empfangen."
            self.lang['recv_ArtPollReply'] = 'ArtPollReply Paket empfangen.'
            self.lang['unknown_OpCode'] = "Paket mit unbekanntem OpCode %s empfangen."
            self.lang['recv_ArtPoll'] = "ArtPoll Paket empfangen."
            self.lang['send_ArtPollReply'] = "ArtPollReply Paket gesendet."
            self.lang['closed'] = "ArtNet Empfaenger beendet."
        elif language == 'English':
            self.lang['ip_address'] = 'Please type in the IP address of this computer: '
            self.lang['listening_for_packets'] = 'Listening for incoming packets...'
            self.lang['invalid_id'] = "Received packet with invalid ID or version."
            self.lang['recv_ArtPollReply'] = 'Received ArtPollReply packet.'
            self.lang['unknown_OpCode'] = "Received packet with unknown OpCode %s."
            self.lang['recv_ArtPoll'] = "Received ArtPoll packet."
            self.lang['send_ArtPollReply'] = "Sending ArtPollReply packet..."
            self.lang['closed'] = "ArtNet receiver closed."

    def server(self):
        self.ip = raw_input(self.lang['ip_address'])
        self.ip = [int(i) for i in self.ip.split('.')]
        print self.lang['listening_for_packets']
        while True:
            data = self.s.recv(2048)
            id8 = data[:8]
            version = struct.unpack('>H', data[10:12])[0]
            if not id8 == 'Art-Net\x00' and version == 14:
                print self.lang['invalid_id']
                continue
            opcode = struct.unpack('<H', data[8:10])[0]
            if opcode == 0x5000:
                self.handle_ArtDMX(data)
            elif opcode == 0x2000:
                self.handle_ArtPoll(data)
            elif opcode == 0x2100:
                print self.lang['recv_ArtPollReply']
            else:
                print self.lang['unknown_OpCode'] % repr(opcode)
    
    def handle_ArtDMX(self, data):
        packet_address_subnet = ord(data[14]) >> 4
        packet_address_universe = ord(data[14]) - (packet_address_subnet << 4)
        packet_address_net = ord(data[15])
        if packet_address_net != self.net or packet_address_subnet != self.subnet:
            return False
        data_length = struct.unpack('>H', data[16:18])[0]
        self.universes[packet_address_universe][1:data_length +1] = [ord(i) for i in data[18:]]
        print 'Valid DMX data received.'

    def set_address(self, net, subnet):
        net = int(net)
        subnet = int(subnet)
        if 0 <= net <= 127 and 0 <= subnet <= 15:
            self.net = net
            self.subnet = subnet
    
    def handle_ArtPoll(self, data):
        print self.lang['recv_ArtPoll']
        self.ArtPollReply()

    def ArtPollReply(self):
        content = []
        # Name, 7byte + 0x00
        content.append("Art-Net\x00")
        # OpCode ArtPollReply -> 0x2100, Low Byte first
        content.append(struct.pack('<H', 0x2100))
        # Protocol Version 14, High Byte first
        content.append(struct.pack('>H', 14))
        # IP
        content += [chr(i) for i in self.ip]
        # Port
        content.append(struct.pack('<H', 0x1936))
        # Firmware Version
        content.append(struct.pack('>H', 200))
        # Net and subnet of this node
        net = 0
        subnet = 0
        content.append(chr(net))
        content.append(chr(subnet))
        # OEM Code (E:Cue 1x DMX Out)
        content.append(struct.pack('>H', 0x0360))
        # UBEA Version -> Nope -> 0
        content.append(chr(0))
        # Status1
        content.append(struct.pack('>H', 0b11010000))
        # Manufactur ESTA Code
        content.append('LL')
        # Short Name
        content.append('luminosus-server2\x00')
        # Long Name
        content.append('luminosus-server2_ArtNet_Node' + '_' * 34 + '\x00')
        # stitch together
        content = ''.join(content)
        print self.lang['send_ArtPollReply']
        port = 6454
        self.s.sendto(content, ("<broadcast>", port))

    def close(self):
        self.s.close()
        print self.lang['closed']
