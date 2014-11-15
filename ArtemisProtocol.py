__author__ = 'Vincent Slotman'
from bitstring import BitArray, Bits
import struct
from Artemis import Ship
from pprint import pprint, pformat

class ArtemisPacketTypes:
    # Known Packet-types from
    # https://github.com/rjwut/ArtClientLib/wiki/Artemis-Packet-Protocol%3A-Packet-Types
    types = {	'0xb83fd2c4': ('BeamFiredPacket',),
                '0xd672c35f': ('CommsIncomingPacket',),
                '0xcc5a3e30': ('DestroyObjectPacket',),
                '0x3de66711': ('DifficultyPacket',),
                '0x077e9f3c': ('EngGridUpdatePacket',),
                '0xf754c8fe': ('GameMessagePacket',),
                '0xae88e058': ('IncomingAudioPacket',),
                '0xee665279': ('IntelPacket',),
                '0x80803df9': ('ObjectStatusUpdatePacket',),
                '0x19c6e2d4': ('ConsoleStatusPacket',),
                '0xe548e74a': ('VersionPacket',),
                '0x6d04b3da': ('WelcomePacket',),
                '0x6aadc57f': ('AudioCommandPacket',),
                '0x574c4c4b': ('CommsOutgoingPacket',),
                '0x809305a7': ('GameMasterMessagePacket',),
                '0x4c821d3c': ('ShipActionPacket', {'0x14': 'KeystrokePacket'}),
                '0x69cc01d9': ('ShipActionPacket',),
                '0x0351a5ac': ('ShipActionPacket',),
            }

    # Map shorthand to bitstring.unpack-fmt
    unpackMap = {  'h':     'intle:16',
                   'c':     'char:16',
                   'i':     'intle:32',
                   'f':     'floatle:32',
                   'b':     'bytes:1',
                   'str':   'bytes',
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
                        18: ('unknown',         'h'),
                        19: ('ship_name',       'str'),
                        20: ("frontshield",     'f'),
                        21: ("frontshieldmax",  'f'),
                        22: ("rearshield",      'f'),
                        23: ("rearshieldmax",   'f'),
                        24: ('dockingstation',  'i'),
                        25: ('redalert',        'b'),
                        26: ('unknown',         'f'),
                        27: ('mainscreen',      'b'),
                        28: ('beamfreq',        'b'),
                        29: ('coolant',         'b'),
                        30: ('unknown',         'i'),
                        31: ('unknown',         'i'),
                        32: ('unknown',         'b'),
                        33: ('unknown',         'i'),
                        34: ('unknown',         'f'),
                        35: ('unknown',         'b'),
                        36: ('unknown',         'f'),
                        37: ('unknown',         'b'),
                        38: ('unknown',         'i'),
                }

    def getByteType(type):
        for byte, name in ArtemisPacketTypes.types.iteritems():
            if isinstance(name[1], str) and name[1] == type:
                return byte
            elif isinstance(name[1], dict):
                for byte, subname in name[1].iteritems():
                    if subname == type:
                        return byte
        return False

class ArtemisPacket(ArtemisPacketTypes):
    def __init__(self, dir, type, payload):
        pass

class Decoder(ArtemisPacket):
    """Decode and handle Artemis packages, updating the ship-status if needed"""
    def __init__(self, ship, mess):
        if len(mess) < 28:
            return

        message = Bits(bytes=mess)
        self.Ship = ship
        # Known packet types according to https://github.com/rjwut/ArtClientLib/wiki/Artemis-Packet-Protocol%3A-Packet-Types
        header, length, origin, _, remaining, pkgtype, payload = message.unpack('bytes:4, bytes:4, bytes:4, bytes:4, bytes:4, bytes:4, bytes')
        pkg = BitArray(bytes=pkgtype)
        pkg.byteswap()

        # Check if we have a known packet-type, then call its method
        if str(pkg) in ArtemisPacket.types:
            getattr(self, ArtemisPacket.types[str(pkg)][0], self.UnknownType)(payload)

    def UnknownType(self, message):
        return
        print 'Unknown MessageType for: %s' % message

    def WelcomePacket(self, message):
        print 'Welcome to Artemis'
        print message[4:]

    def BeamsFiredPacket(self, message):
        vals = None
        try:
            vals = struct.unpack("iiiiiiiiiii", message[24:])
            if vals[2] == 1:
                if vals[6] == self.shipId:
                    print "WE GOT HIT!"
                    print "Damageteam from %i to %i" % (vals[5:7])

        except struct.error:
            print "unpack error"

    def ObjectStatusUpdatePacket(self, message):
        msg = Bits(bytes=message)
        if msg == '0x00000000':
            return False

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
            pprint(Ship.shipStats)

    def EngGridUpdatePacket(self, message):
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
                    print " ", "--" * 20
                    x, y, z = [ord(p) for p in toDec[0:3]]
                    coord = "%i%i%i" % (x, y, z)
                    subName = self.Ship.shipMap.get(coord, 'unmapped')
                    print "Subsystem [%s] damage at x:%i y:%i z:%i - damage now: %f" % (subName, x, y, z, damage)
                    #     #DMXstart = self.DMXmapping[coord]
                    #     #print subName, DMXstart, coord, damage
                    #     #self.DMXvalues[DMXstart] = int(damage * 80)
                    #     #self.DMXvalues[DMXstart + 1] = int(60 - (damage * 60))
                    #     #ArtNetModule.ArtDMX_broadcast(self.DMXvalues, self.ArtNetServerIP)
                    #     #print "Sending DMX: (subName, DMX): (%s, %s) ", (subName, str(self.DMXvalues))
                else:
                    break

    def  DifficultyPacket(self, message):
        print "SIM START", message[20:]
        Ship.shipId = 0
