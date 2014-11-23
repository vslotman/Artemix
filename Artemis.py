import struct
from collections import Counter

class SystemHealth(dict):
    """Container for Engineering-node health. Calls all IO-senders if data gets updated"""
    def __init__(self, shipMap, IO):
        # Build map of system-type and nodes
        # Fill it with 1's to signify healthy ship
        self.IO_enabled = False
        self.IO = IO

        for coord, name in shipMap.iteritems():
            self[coord] = [name, 1]
        self.IO_enabled = True

    def __setitem__(self, key, value):
        super(SystemHealth, self).__setitem__(key, value)
        if self.IO_enabled:
            self.IO.send_data(systemhealth=self)


    def update(self, *args, **kwargs):
        if args:
            if len(args) > 1:
                raise TypeError("update expected at most 1 arguments, "
                                "got %d" % len(args))
            other = dict(args[0])
            for key in other:
                self[key] = other[key]
        for key in kwargs:
            self[key] = kwargs[key]

    def setdefault(self, key, value=None):
        if key not in self:
            self[key] = value
        return self[key]


class Ship:
    """Contains runtime and static data of the ship"""
    shipStats = {}
    shipID = -1

    def __init__(self, sntFile, IO):
        #load the ship data from the snt file
        print "Setting up ship..."
        self.shipMap, self.dmxMap = self.loadShipData(sntFile)
        self.IO = IO
        # nowe we know the coords of ship systems count the number of each
        # ship systems can be calculated.
        # This is how the client does it... warp: 25% means 1 out of 4 nodes isnt
        # damaged
        self.systemCount = Counter(self.shipMap.values())
        self.systemHealth = SystemHealth(self.shipMap, IO)

    def loadShipData(self, sntFile):
        """load ship data from the snt file."""
        maxX = 5
        maxY = 4
        maxZ = 9
        x, y, z = 0, 0, 0
        shipMap = {}
        ship2d = [0 for i in range(50)]
        value = x

        namemap = ["Primary Beam", "Torpedo", "Tactical", "Maneuver", "Impulse", "Warp", "Front Shield", "Rear Shield"]

        print "Loading engineering-nodes from %s.." % sntFile
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
                shipMap[key] = "unknown"
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
        #dmxMap = {}
        dmxMap = False
        #for i in range(0, len(shipMap.keys())):
        #    dmxMap.update(sorted(shipMap.keys()[i]), (i+1)*3)
        return shipMap, dmxMap