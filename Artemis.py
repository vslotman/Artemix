import socket
import struct
import ArtNetModule
from collections import Counter

class Decoder:

	def __init__(self, sntFile, ArtNetIP):
		#the current Ship ID
		self.shipId = 0
		# ship stats
		self.shipStats = {"shield": -1, "energy" : -1 ,"coordY" : -1, "coordX" : -1, "warp rate" : -1,"rotation rate" : -1, "impulse rate" : -1, "unknown" : -1, "unknown2" : -1, "rotation":-1, "frontshield" : -1, "rearshield" : -1, "weaponlock" : -1, "autobeams": -1, "speed": -1}

		#a map of bitfield position to value name and type
		self.statMapHelm = {15 : ("energy", 'f'), 21: ("coordY", 'f'), 19: ("coordX", 'f'), 16: ("shield", 'h'), 14: ("warp rate", 'b'), 10:("rotation rate", 'f'), 9: ("impulse rate", 'f'),  23: ("unknown2", 'f'), 25: ("speed", 'f'), 24: ("rotation", 'f'), 28: ("frontshield",'f'), 30: ("rearshield", 'f'), 8: ("weaponlock", "i"), 13:("autobeams",'b')}

		#sizes of struct fmt types. struct.calcsize returns size including alignment which this seems to ignore sometimes
		self.numLens = { 'f' : 4, 'h' : 2, 'i' : 4, 'b' : 1}
		
		#DMX initialisieren
		self.DMXvalues = [0]*49 + [0,60,0]*37
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


	'''
	load ship data from the snt file
	only loads nodes that have a subsystem assigned to them
	'''
	def loadShipData(self, sntFile):
		maxX = 5
		maxY = 4
		maxZ = 9
		x,y,z = 0,0,0
		shipMap = {}
		ship2d = [0 for i in range(50)]
		value = x

		namemap = ["Primary Beam", "Torpedo", "Tactical", "Maneuver", "Impulse", "Warp", "Front Shield", "Rear Shield"]
		
		print "loading snt file.."
		f = open(sntFile, "r")

		for block in iter(lambda: f.read(32), ""):
			
			coords =  struct.unpack("fff", block[0:12])

			#print [ord(p) for p in block[12:] ], coords
			if ord(block[12]) < 254:
				key = "%i%i%i"%(x,y,z)
				print key,"=",namemap[ord(block[12])]				
				shipMap[key] = namemap[ord(block[12])]
			if ord(block[12]) == 255:
                                key = "%i%i%i"%(x,y,z)
                                print key,"=", "unmapped"				
				shipMap[key] = "unmapped"
			if ord(block[12]) != 254: 
                                key2 = int("%i%i"%(x,z))
                                ship2d[key2] += 1
                                #print key2,ship2d[key2]
			#print x,y,z,ord(block[12])
			if z < maxZ:
				z += 1
			else:
				z = 0
				if y < maxY:
					y += 1
				else :
					y = 0
					x += 1
					x %= maxZ
		print "..done"
		print self.DMXmapping
		ArtNetModule.ArtDMX_broadcast(self.DMXvalues, self.ArtNetServerIP)
		print shipMap
		return shipMap

			
	''' Decode a 32bit int to a binary value as a string
		also return number of bits set to 1
	'''
	def decBitField(self, bitstr):
		valcount = 0
		outstr = ""
		for i in range (0,32):
			bit = bitstr & (1 << i)
			if(bit > 0):
				valcount += 1
				outstr += "1"
			else :
				outstr += "0"
		return (valcount, outstr)

	''' decode a packet using a map of bitfield -> statname
	'''
	def decodePacket(self, bitStr, message, statsMap):
		valPtr = 0
		goodPacket = True
		tempResults = {}
		bound = 0
		for i in range(32):
			if bitStr  & (1 << i) > 0:
				try:
					mappedStat = statsMap[i]
					bound = self.numLens[mappedStat[1]]
					tempResults[mappedStat[0]] = struct.unpack(mappedStat[1], message[valPtr : valPtr + bound])
				except:
					goodPacket = False

				valPtr += bound
		st = ""
		if goodPacket:
			for stat in tempResults:
				self.shipStats[stat] = tempResults[stat]
				st = str(self.shipStats)
			return st
		else:
			return None
		



	def processPacket(self, message):
		if len(message) == 0:
			return
		mess = [ord(p) for p in message]

		messType = mess[16:20]

		''' ship state data
			sent to all connected clients, even those that arent
			assigned a station
		'''
			
		if  messType ==  [0xf9,0x3d,0x80,0x80]:
			if mess[20:24] == [0,0,0,0] or len(mess[24:]) == 0:
				return
			else:
				playerShip = mess[20]
				if playerShip == 0x01:
					sId = struct.unpack("h", message[21:23])
					if self.shipId == 0:
						self.shipId = sId[0]
						print "GOT SHIP ID:", self.shipId

					c = struct.unpack("i", message[24:28])[0]

					v = self.decBitField(c)
					a = self.decodePacket(c, message[36:],self.statMapHelm)

		elif messType == [0xc4, 0xd2, 0x3f, 0xb8]:
			vals = None
			try:
				vals = struct.unpack("iiiiiiiiiii", message[24:])
				if vals[2] == 1:
					if vals[6] == self.shipId:
						print "WE GOT HIT!"
						#print "Damageteam from %i to %i" %(vals[5:7])


			except struct.error:
				print "unpack error"


		elif messType == [0xfe, 0xc8, 0x54, 0xf7]:
			#print "global? " , mess[20:]
			if mess[20:24] == [0,0,0,0]:
				print "global? " , mess[20:]
				if mess[24] == 1:
					#get ship id
					ship = struct.unpack("i", message[28:32])[0]
					print "ship asplode: ", ship
					if ship == self.shipId:
						print "KABOOM SHIP ASPLODED!"

		elif messType == [0x30, 0x3e, 0x5a, 0xcc]:
			pass
		elif messType == [0x3c,0x9f,0x7e,0x7]:
			#print "engineering packet"

			if mess[21] == 255:
				pass
				#print "print damage crew moving"
			else :
		#		print mess[20:]
				for i in range(0, len(mess[21:]), 7):
					toDec = message[21 + i : 21 + i+7]

					if ord(toDec[0]) != 255:
						damage = struct.unpack("f", toDec[3:7])[0]
						#print "Subsystem damage " ,"--" * 20
						x,y,z = [ord(p) for p in toDec[0:3]]
						#print ".. at x:%i y:%i z:%i - damage now: %f" %(x,y,z, damage)
						try:
							coord = "%i%i%i" % (x,y,z)
							subName = self.shipMap[coord]
							DMXstart = self.DMXmapping[coord]
							print subName, DMXstart, coord, damage
							self.DMXvalues[DMXstart] = int(damage*80)
							self.DMXvalues[DMXstart+1] = int(60-(damage*60))
							ArtNetModule.ArtDMX_broadcast(self.DMXvalues, self.ArtNetServerIP)
							#print "..which is mapped to ", subName
						except KeyError:
							print "..not a mapped system"

					else:
						break
				#print mess[20:]
		elif messType == [0x26, 0x12, 0x82, 0xf5]:
			pass

		elif messType == [0x11, 0x67, 0xe6, 0x3d]:
			print "SIM START", mess[20:]
			self.shipId = 0


		else:
			if messType == []:
				return
			print "UNKNOWN " ,"--" * 20
			print [hex(p) for p in messType]
			print mess


