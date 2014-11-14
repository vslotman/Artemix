import socket
import struct
import ArtNetModule
from collections import Counter
from pprint import pprint
from bitstring import BitArray, BitStream, Bits

# http://www.pyinstaller.org/

class Ship:
    """Contains runtime and static data of the ship"""
    shipStats = {}
    shipID = -1

    def __init__(self, sntFile):
        #load the ship data from the snt file
        self.shipMap = self.loadShipData(sntFile)
        # nowe we know the coords of ship systems count the number of each
        # ship systems can be calculated.
        # This is how the client does it... warp: 25% means 1 out of 4 nodes isnt
        # damaged
        self.systemCount = Counter(self.shipMap.values())

    def loadShipData(self, sntFile):
        """load ship data from the snt file. Only loads nodes that have a subsystem assigned to them"""
        maxX = 5
        maxY = 4
        maxZ = 9
        x, y, z = 0, 0, 0
        shipMap = {}
        ship2d = [0 for i in range(50)]
        value = x

        namemap = ["Primary Beam", "Torpedo", "Tactical", "Maneuver", "Impulse", "Warp", "Front Shield", "Rear Shield"]

        print "loading snt file.."
        f = open(sntFile, "r")

        for block in iter(lambda: f.read(32), ""):

            coords = struct.unpack("fff", block[0:12])

            # print [ord(p) for p in block[12:] ], coords
            if ord(block[12]) < 254:
                key = "%i%i%i" % (x, y, z)
                #print key, "=", namemap[ord(block[12])]
                shipMap[key] = namemap[ord(block[12])]
            if ord(block[12]) == 255:
                key = "%i%i%i" % (x, y, z)
                #print key, "=", "unmapped"
                shipMap[key] = "unmapped"
            if ord(block[12]) != 254:
                key2 = int("%i%i" % (x, z))
                ship2d[key2] += 1
                #print key2,ship2d[key2]
            #print x,y,z,ord(block[12])
            if z < maxZ:
                z += 1
            else:
                z = 0
                if y < maxY:
                    y += 1
                else:
                    y = 0
                    x += 1
                    x %= maxZ
        print "..done"
        #pprint(self.DMXmapping)
        #ArtNetModule.ArtDMX_broadcast(self.DMXvalues, self.ArtNetServerIP)
        #pprint(shipMap)
        return shipMap

class Decoder:
    def __init__(self, sntFile, ArtNetIP):
        # the current Ship ID
        self.shipId = 0

        #sizes of struct fmt types. struct.calcsize returns size including alignment which this seems to ignore sometimes
        self.numLens = {'f': 4, 'h': 2, 'i': 4, 'b': 1}

        #DMX initialisieren
        self.DMXvalues = [0] * 49 + [0, 60, 0] * 37
        self.ArtNetServerIP = ArtNetIP
        self.DMXmapping = {
            "013": 112,
            "026": 100,
            "029": 58,
            "031": 115,
            "033": 109,
            "036": 103,
            "039": 55,
            "121": 121,
            "127": 82,
            "129": 61,
            "131": 118,
            "210": 130,
            "212": 136,
            "219": 70,
            "221": 133,
            "227": 85,
            "228": 76,
            "230": 127,
            "239": 52,
            "240": 124,
            "247": 79,
            "248": 73,
            "321": 142,
            "327": 88,
            "329": 64,
            "331": 139,
            "413": 157,
            "426": 94,
            "429": 67,
            "431": 145,
            "433": 151,
            "436": 91,
            "439": 49,

        }
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        #load the ship data from the snt file
        self.shipMap = self.loadShipData(sntFile)
        # nowe we know the coords of ship systems count the number of each
        # ship systems can be calculated.
        # This is how the client does it... warp: 25% means 1 out of 4 nodes isnt
        # damaged
        self.systemCount = Counter(self.shipMap.values())




    ''' Decode a 32bit int to a binary value as a string
        also return number of bits set to 1
    '''

    def decBitField(self, bitstr):
        valcount = 0
        outstr = ""
        for i in range(0, 32):
            bit = bitstr & (1 << i)
            if (bit > 0):
                valcount += 1
                outstr += "1"
            else:
                outstr += "0"
        return (valcount, outstr)

    def decodePacket(self, bitStr, message, statsMap):
        valPtr = 0
        goodPacket = True
        tempResults = {}
        bound = 0
        print "Decoding Packets...."
        for i in range(32):
            if bitStr & (1 << i) > 0:
                try:
                    mappedStat = statsMap[i]
                    print (('mappedStat', mappedStat))
                    bound = self.numLens[mappedStat[1]]
                    print (('bound', bound))
                    print (('message[valPtr: valPtr + bound]', message[valPtr: valPtr + bound]))
                    tempResults[mappedStat[0]] = struct.unpack(mappedStat[1], message[valPtr: valPtr + bound])
                except:
                    goodPacket = False

                valPtr += bound
        st = ""

        if goodPacket:
            # Hier komt ie nooit
            for stat in tempResults:
                self.shipStats[stat] = tempResults[stat]
                st = str(self.shipStats)
            print '# SHIP STATS #####################'
            pprint(self.shipStats)
            print '#####################'
            return st
        else:
            return None

    def processPacket(self, message):
        if len(message) == 0:
            return
        mess = [ord(p) for p in message]
        messType = mess[16:20]
        #pprint(mess)
        ''' ship state data
            sent to all connected clients, even those that arent
            assigned a station
        '''

        if messType == [0xf9, 0x3d, 0x80, 0x80]:
            # Object status update packet (0x80803df9)
            # DroneUpdatePacket (subtype 0x10)
            # EngPlayerUpdatePacket (subtype 0x03)
            # GenericMeshPacket (subtype 0x0d)
            # GenericUpdatePacket (subtypes 0x06, 0x07, 0x0a-0x0c, 0x0e)
            # MainPlayerUpdatePacket (subtype 0x01)
            # NebulaUpdatePacket (subtype 0x09)
            # NpcUpdatePacket (subtype 0x04)
            # BasePacket (subtype 0x05)
            # WeapPlayerUpdatePacket (subtype 0x02)
            # WhaleUpdatePacket (subtype 0x0f)
            if mess[20:24] == [0, 0, 0, 0] or len(mess[24:]) == 0:
                return
            else:
                playerShip = mess[20]
                if playerShip == 0x01:
                    sId = struct.unpack("h", message[21:23])
                    if self.shipId == 0:
                        self.shipId = sId[0]
                        print "GOT SHIP ID:", self.shipId
                        print mess

                    c = struct.unpack("i", message[24:28])[0]

                    v = self.decBitField(c)
                    print v, c
                    a = self.decodePacket(c, message[36:], self.statMapHelm)

        elif messType == [0xc4, 0xd2, 0x3f, 0xb8]:
            # https://github.com/rjwut/ArtClientLib/wiki/Artemis-Packet-Protocol%3A-BeamFiredPacket
            # Packet type: 0xb83fd2c4, direction: in
            # Notifies the client that beam weapon has been fired.

            vals = None
            try:
                vals = struct.unpack("iiiiiiiiiii", message[24:])
                if vals[2] == 1:
                    if vals[6] == self.shipId:
                        print "WE GOT HIT!"
                        print "Damageteam from %i to %i" % (vals[5:7])

            except struct.error:
                print "unpack error"
        elif messType == [0xfe, 0xc8, 0x54, 0xf7]:
            # Game message packet (0xf754c8fe)
            # AllShipSettingsPacket (subtype 0x0f)
            # DmxMessagePacket (subtype 0x10)
            # GameMessagePacket (subtype 0x0a)
            # GameOverPacket (subtype 0x06)
            # GameOverReasonPacket (subtype 0x14)
            # GameOverStatsPacket (subtype 0x15)
            # GameStartPacket (subtype 0x00)
            # JumpStatusPacket (subtypes 0x0c and 0x0d)
            # KeyCaptureTogglePacket (subtype 0x11)
            # PlayerShipDamagePacket (subtype 0x05)
            # SkyboxPacket (subtype 0x09)
            # SoundEffectPacket (subtype 0x03)
            print "global? ", mess[20:]
            print mess
            pprint(self.shipStats)
            print '===================='
            if mess[20:24] == [0, 0, 0, 0]:
                print "global? ", mess[20:]
                if mess[24] == 1:
                    # get ship id
                    ship = struct.unpack("i", message[28:32])[0]
                    print "ship asplode: ", ship
                    if ship == self.shipId:
                        print "KABOOM SHIP ASSPLODED!"

        elif messType == [0x30, 0x3e, 0x5a, 0xcc]:
            # https://github.com/rjwut/ArtClientLib/wiki/Artemis-Packet-Protocol%3A-DestroyObjectPacket
            # DestroyObjectPacket (0xcc5a3e30)
            # Packet type: (0xcc5a3e30), direction: in
            # Notifies the client that an object has been removed from play.
            # Payload
            #     Target type (byte)
            #         Indicates the type of object being destroyed. (see Enumerations)
            #     Target ID (int)
            #         ID of the object being destroyed.
            pass
        elif messType == [0x58, 0xe0, 0x88, 0x3c]:
            # https://github.com/rjwut/ArtClientLib/wiki/Artemis-Packet-Protocol%3A-IncomingAudioPacket
            # IncomingAudioPacket (0xae88e058)
            # Packet type: 0xae88e058, direction: in
            # Informs the client of incoming audio messages (used in custom scenarios).
            #
            # Payload
            #     ID (int)
            #         The audio message ID.
            #     Audio Mode (int)
            #         There are two possible values: 0x01 (playing) or 0x02 (incoming).
            #         "Incoming" means that the communications officer is to be notified that an audio message is available, and offered the option to play it or dismiss it.
            #         "Playing" is given in response to the communications officer giving the instruction to play the message,
            #         and notifies them that the message is now being played by the server.
            #         In the stock client, this results in the "Play" button changing to "REPlay."
            #
            #     Title (string, only for incoming mode)
            #         Title of the incoming message. This should be displayed to the COMMs officer.
            #     File (string, only for incoming mode)
            #         The filename for the audio clip. The client doesn't need to do anything with this string; as the audio is played by the server.
            pass
        elif messType == [0x3c, 0x9f, 0x7e, 0x7]:
            # https://github.com/rjwut/ArtClientLib/wiki/Artemis-Packet-Protocol%3A-EngGridUpdatePacket
            # System grid status (array)
            # This contains a list of system nodes, terminated with 0xff. Each system node is formatted as follows:
            #
            # - X coordinate (byte)
            # - Y coordinate (byte)
            # - Z coordinate (byte)
            # - Damage (float)

                        # print "engineering packet"

            if mess[21] == 255:
                #print "print damage crew moving"
                pass
            else:
                print mess[20:]
                for i in range(0, len(mess[21:]), 7):
                    toDec = message[21 + i: 21 + i + 7]

                    if ord(toDec[0]) != 255:
                        damage = struct.unpack("f", toDec[3:7])[0]
                        print " ", "--" * 20
                        x, y, z = [ord(p) for p in toDec[0:3]]
                        print "Subsystem damage at x:%i y:%i z:%i - damage now: %f" % (x, y, z, damage)
                        try:
                            coord = "%i%i%i" % (x, y, z)
                            subName = self.shipMap[coord]
                            DMXstart = self.DMXmapping[coord]
                            print subName, DMXstart, coord, damage
                            self.DMXvalues[DMXstart] = int(damage * 80)
                            self.DMXvalues[DMXstart + 1] = int(60 - (damage * 60))
                            ArtNetModule.ArtDMX_broadcast(self.DMXvalues, self.ArtNetServerIP)
                            #print "Sending DMX: (subName, DMX): (%s, %s) ", (subName, str(self.DMXvalues))
                        except KeyError:
                            print "..not a mapped system"

                    else:
                        print mess[20:]
                        break

        elif messType == [0x26, 0x12, 0x82, 0xf5]:
            # Emitted frequently, but no apparent purpose (contains no additional data). Heartbeat packet, perhaps?
            pass

        elif messType == [0x11, 0x67, 0xe6, 0x3d]:
            # https://github.com/rjwut/ArtClientLib/wiki/Artemis-Packet-Protocol%3A-DifficultyPacket
            # Packet type: 0x3de66711, direction: in
            # Informs clients of the difficulty level when starting or connecting to a game.
            # Payload
            #     Difficulty (int)
            #         The difficulty level (a value from 1 to 11)
            #     Game type (int)
            #         A value indicating the type of game. Applies only to solo and co-op games,
            #         field is present but value is undefined for PvP and scripted games. See Enumerations, Game type.
            print "SIM START", mess[20:]
            self.shipId = 0
        else:
            if messType == []:
                return
            print "UNKNOWN ", "--" * 20
            print [hex(p) for p in messType]
            #print mess


