from luminosus import ArtNet
import sys, inspect
import socket
import struct

class ArtNet_Sender(ArtNet.ArtNet_Sender):
    def __init__(self, **kwargs):
        # Copy of luminosus-class, but with added support for sending- and receiving ArtNet packet
        print 'Constructing ArtNet Sender'
        artnet_method  = kwargs.get('artnet_method', 'broadcast')
        artnet_address = kwargs.get('artnet_address', (0,0,0))
        existing_socket = kwargs.get('socket')

        self.dmx_mappings = kwargs.get('dmx_mappings', {})
        self.data = [0] * 512

        self.create_lang_dict()
        self.nodes = []
        self.manually_added_nodes = []
        self.sending_method = artnet_method
        if existing_socket:
            self.s = existing_socket
        else:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.s.bind(("", 6454))
        self.build_header(artnet_address)
        self.ArtPoll()

    def artemis_send(self, data):
        self.send_dmx_data(self._process_data(**data))

    def _process_data(self, **kwargs):
        if 'systemhealth' in kwargs:

            pos, end = self.dmx_mappings.get('subsystem_health', (8, 170))
            systems = {}
            for coord, stats in sorted(kwargs['systemhealth'].iteritems()):
                systems.setdefault(stats[0], [])
                systems[stats[0]].append(stats[1])
                if pos <= end and pos < 513:
                    self.data[pos] = int(stats[1] * 255)
                pos += 1

            pos, end = self.dmx_mappings.get('system_health', (0, 7))
            for key, val in sorted(systems.iteritems()):
                self.data[pos] = int((sum(val)/len(val)) * 255)
                pos += 1
                if pos > end or pos > 512:
                    break
        return self.data

class ArtNet_Receiver:
    def __init__(self, **kwargs):
        self.net, self.subnet, self.universe = kwargs.get('artnet_address', (0,0,0))

        print 'Constructing ArtNet Receiver'
        self.rcv = ArtNet.ArtNet_Receiver(ip=kwargs.get('ip', ''))

    def get_socket(self):
        return self.rcv.s

    def handle_data(self, data):
        retval = False
        id8 = data[:8]
        version = struct.unpack('>H', data[10:12])[0]
        if not id8 == 'Art-Net\x00' and version == 14:
            return
        opcode = struct.unpack('<H', data[8:10])[0]
        if opcode == 0x5000:
            retval = self.rcv.handle_ArtDMX(data)
        elif opcode == 0x2000:
            self.rcv.handle_ArtPoll(data)
        elif opcode == 0x2100:
            print self.rcv.lang['recv_ArtPollReply']
        else:
            print self.rcv.lang['unknown_OpCode'] % repr(opcode)

        if retval != False:
            return self.rcv.universes


# class Artemis_Receiver:
#     def __init__(self, **kwargs):
#         ip = kwargs.get('ip', 'localhost')
#         port = kwargs.get('port', 6545)
#         client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         client.bind((ip, port))
#         client.listen(1)
#         print "Waiting for connection from client on %s:%s .." % (ip, port)
#         #serverSock = None
#
#         (self.toClientSock, addr) = client.accept()
#         print "got connection from ", addr
#
#     def get_socket(self):
#         return self.toClientSock

    # def __init__(self, kwargs):
    #     ip = kwargs.get('ip', 'localhost')
    #     port = kwargs.get('port', 6545)
    #     asyncore.dispatcher.__init__(self)
    #     self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
    #     self.bind((ip, port))
    #     self.listen(1)
    #     print "Waiting for connection from client on %s:%s .." % (ip, port)
    #     #serverSock = None

# class Artemis_Sender:
#     def __init__(self, **kwargs):
#         ip = kwargs.get('ip', 'localhost')
#         port = kwargs.get('port', 6545)
#         print "conecting to artemis server at", ip
#         self.artemis_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         self.artemis_server.connect((ip, port))
#         print "..connected"
#
#     def get_socket(self):
#         return self.artemis_server

class Sender:
    def __init__(self, **kwargs):
        clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
        self.senders = []

        for cl in clsmembers:
            print kwargs.get(cl[0], {})
            if hasattr(cl[1], 'artemis_send'):
                self.senders.append((cl[0], cl[1](**kwargs.get(cl[0], {}))))

    def send_data(self, **kwargs):
        data = []
        #print kwargs
        for fun, sender in self.senders:
            print 'Sending data using method <%s>' % fun
            sender.artemis_send(kwargs)

# class Receiver:
#     def __init__(self, **kwargs):
#         clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)
#         self.receivers = []
#
#         for cl in clsmembers:
#             print kwargs.get(cl[0], {})
#             if hasattr(cl[1], 'artemis_receive'):
#                 self.receivers.append((cl[0], cl[1](kwargs.get(cl[0], {}))))
#
#     def get_sockets(self):
#         for rcv in self.receivers:
#             yield rcv[1].get_socket()


