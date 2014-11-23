__author__ = 'Vincent Slotman'
from bitstring import BitArray, Bits, pack
import struct
from Artemis import Ship

class ArtemisPacketTypes:
    # Known Packet-types from
    # https://github.com/rjwut/ArtClientLib/wiki/Artemis-Packet-Protocol%3A-Packet-Types
    # Changed endian-ness to skip unnecessary byteswaps
    packet_type = {'0x7fc5ad6a': ('AudioCommandPacket', False),
                    '0xc4d23fb8': ('BeamFiredPacket', False),
                    '0x5fc372d6': ('CommsIncomingPacket', False),
                    '0x4b4c4c57': ('CommsOutgoingPacket', False),
                    '0xd4e2c619': ('ConsoleStatusPacket', False),
                    '0x303e5acc': ('DestroyObjectPacket', False),
                    '0x1167e63d': ('DifficultyPacket', False),
                    '0x3c9f7e07': ('EngGridUpdatePacket', False),
                    '0xa7059380': ('GameMasterMessagePacket', False),
                    '0xfec854f7': ('GameMessagePacket', False),
                    '0x58e088ae': ('IncomingAudioPacket', False),
                    '0x795266ee': ('IntelPacket', False),
                    '0xf93d8080': ('ObjectStatusUpdatePacket',
                                   {'0x01': 'MainPlayerUpdatePacket',
                                    '0x04': 'NpcUpdatePacket'}),
                    '0x3c1d824c': ('ShipActionPacket0',
                                   {'0x04': 'ToggleShieldsPacket',
                                    '0x14': 'KeystrokePacket',
                                    '0x08': 'FireTubePacket'}),
                    '0xd901cc69': ('ShipActionPacket1', False),
                    '0xaca55103': ('ShipActionPacket2', False),
                    '0x4ae748e5': ('VersionPacket', False),
                    '0xdab3046d': ('WelcomePacket', False),
               }

    # Map shorthand to bitstring.unpack-fmt
    # Todo: A string is enclosed in 0x00
    unpackMap = {  'h':     'intle:16',
                   'c':     'char:16',
                   'i':     'intle:32',
                   'f':     'floatle:32',
                   'b':     'bytes:1',
                   'str':   'bytes',
                 }

    # Map of packet-name, its identifier and shorthand format-string for packing
    type_packet = {'ToggleShieldsPacket':       ('0x3c1d824c04', 'i:0'),
                   'FireTubePacket':            ('0x3c1d824c08', 'i:%i'),
                   'GameMasterMessagePacket':   ('0xfec854f7', 'str:%s, str:%s'),
                   }


    # Type-map of MainPlayerUpdatePacket payload
    # https://github.com/rjwut/ArtClientLib/wiki/Artemis-Packet-Protocol%3A-MainPlayerUpdatePacket
    MPUP_statusmap = {  0: ("weaponlock",       'i'),
                        1: ("impulse",          'f'),
                        2: ("rudder",           'f'),
                        3: ("topspeed",         'f'),
                        4: ('turnrate',         'f'),
                        5: ("autobeams",        'b'),
                        6: ("warprate",         'b'),
                        7: ("energy",           'f'),
                        8: ("shield",           'h'),
                        9: ('ship_number',      'i'),
                        10: ('ship_type',       'i'),
                        11: ("coordX",          'f'),
                        12: ("coordY",          'f'),
                        13: ("coordZ",          'f'),
                        14: ("pitch",           'f'),
                        15: ('roll',            'f'),
                        16: ("heading",         'f'),
                        17: ("speed",           'f'),
                        18: ('unknown18',         'h'),
                        19: ('ship_name',       'str'),
                        20: ("frontshield",     'f'),
                        21: ("frontshieldmax",  'f'),
                        22: ("rearshield",      'f'),
                        23: ("rearshieldmax",   'f'),
                        24: ('dockingstation',  'i'),
                        25: ('redalert',        'b'),
                        26: ('unknown26',         'f'),
                        27: ('mainscreen',      'b'),
                        28: ('beamfreq',        'b'),
                        29: ('coolant',         'b'),
                        30: ('unknown30',         'i'),
                        31: ('unknown31',         'i'),
                        32: ('unknown32',         'b'),
                        33: ('unknown33',         'i'),
                        34: ('unknown34',         'f'),
                        35: ('unknown35',         'b'),
                        36: ('unknown36',         'f'),
                        37: ('unknown37',         'b'),
                        38: ('unknown38',         'i'),
                }


class ArtemisDecoder(ArtemisPacketTypes):
    """Decode and handle Artemis packages, updating the ship-status if needed"""
    def __init__(self, ship):
        self.Ship = ship

    def decode(self, mess):
        if len(mess) < 28:
            return
        message = Bits(bytes=mess)

        # Known packet types according to https://github.com/rjwut/ArtClientLib/wiki/Artemis-Packet-Protocol%3A-Packet-Types
        header, length, origin, _, remaining, pkgtype, payload = message.unpack('bytes:4, bytes:4, bytes:4, bytes:4, bytes:4, bytes:4, bytes')
        pkg = BitArray(bytes=pkgtype)

        # Check if we have a known packet-type, then call its method
        if str(pkg) in ArtemisPacketTypes.packet_type:
            getattr(self, ArtemisPacketTypes.packet_type[str(pkg)][0],
                    self.UnknownType)(payload, ArtemisPacketTypes.packet_type[str(pkg)][1])

    def UnknownType(self, message, types):
        msg = Bits(bytes=message)
        #print 'Unknown MessageType for: %s' % msg.hex

    def ShipActionPacket0(self, message, types):
        msgtype, payload = msg.unpack('bytes:1, bytes')
        # ToggleShieldsPacket
        #print '###############################################################'
        #print self.message
        if Bits(bytes=msgtype) == '0x04':
            #print self.message
            pass

    def WelcomePacket(self, message, types):
        print 'Welcome to Artemis'
        print message[4:]

    def BeamsFiredPacket(self, message, types):
        vals = None
        try:
            vals = struct.unpack("iiiiiiiiiii", message[24:])
            if vals[2] == 1:
                if vals[6] == self.shipId:
                    print "WE GOT HIT!"
                    print "Damageteam from %i to %i" % (vals[5:7])

        except struct.error:
            print "unpack error"

    def ObjectStatusUpdatePacket(self, message, types):
        msg = Bits(bytes=message)
        if msg == '0x00000000':
            return

        msgtype, objid, bitfield, payload = msg.unpack('bytes:1, bytes:4, bytes:5, bytes')

        # Subtype MainPlayerUpdatePacket
        if Bits(bytes=msgtype) == '0x01':
            keys = []
            fmt  = []
            # Convert endian-ness and loch-ness of bitfield
            bf = BitArray(bytes=bitfield)
            bf.reverse()
            bf.byteswap()

            # Scan bitfield
            for i in range(0, len(bf)):
                if bf[i]:
                    # Lookup type and length of data
                    key, f = self.MPUP_statusmap.get(i, ('unknown', 'i'))
                    if f[0] == 'unknown':
                        print 'Unknown: %i' % i
                    # Build list of keys and their unpack-fmt-strings
                    keys.append(key)
                    fmt.append(self.unpackMap[f])

            # Unpack the payload, zip everything to a dict and update ship-data
            vals = Bits(bytes=payload).unpack(',  '.join(fmt))
            self.Ship.shipStats.update(dict(zip(keys, vals)))
            #pprint(Ship.shipStats)

    def EngGridUpdatePacket(self, message, types):
        #message = message[4:]
        #msg = Bits(bytes=message)
        if message[0] == 255:
            print "print damage crew moving"
            pass
        else:
            #print Bits(bytes=message)
            for i in range(0, len(message[1:]), 7):
                toDec = message[1 + i: 1 + i + 7]

                if ord(toDec[0]) != 255:
                    damage = struct.unpack("f", toDec[3:7])[0]
                    #print "--" * 20
                    x, y, z = [ord(p) for p in toDec[0:3]]
                    coord = "%i%i%i" % (x, y, z)
                    subName, health = self.Ship.systemHealth[coord]
                    self.Ship.systemHealth[coord] = [subName, 1-damage]
                    print 'Taking damage!'

                else:
                    break

    def  DifficultyPacket(self, message, types):
        print "SIM START", message[20:]
        Ship.shipId = 0

class DMXDecoder:
    def __init__(self, dmxmap):
        self.dmxmap = dmxmap


def pack_payload(fmt='', payload=[]):
    """Pack the payload of a packet using format-string and optional data"""
    if len(payload) != fmt.count('%'):
        return
    format = []
    data = []
    payload = iter(payload)
    for item in fmt.split(', '):
        m, d = item.split(':')
        if '%' in d:
            d = d % payload.next()
        data.append(d)
        format.append(ArtemisPacketTypes.unpackMap[m])

    return pack(', '.join(format), *data)

def build_packet(type, payload=[], origin=2):
    """Builds a packet"""
    packet = ArtemisPacketTypes.type_packet.get(type)
    if packet:
        #print type
        pkg = BitArray(hex=packet[0])
        if packet[1]:
            pkg += pack_payload(packet[1], payload)

        header = Bits(hex='0xefbeadde').bytes
        padding = 0
        remaining = len(pkg) / 8
        length = remaining + 20

        complete = pack('bytes:4, intle:32, intle:32, intle:32, intle:32, bytes', *(header, length, origin, padding, remaining, pkg.bytes))
        return complete.bytes