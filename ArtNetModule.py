import struct
import socket

def ArtDMX_broadcast(dmxdata, ArtNetServerIP):

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    #
    # Taken and modified from luminosus_1.9.3_ArtNet_library
    # published at https://code.google.com/p/luminosus/
    # under GNU GPL v3
    #
    # Thanks a lot!
    #

    # broadcast ip
    ip = ArtNetServerIP
    # UDP ArtNet Port
    port = 6454
    # Universe
    address = [0, 0, 1]
    content = []
    # Name, 7byte + 0x00
    content.append("Art-Net" + "\x00")
    # OpCode ArtDMX -> 0x5000, Low Byte first
    content.append(struct.pack('<H', 0x5000))
    # Protocol Version 14, High Byte first
    content.append(struct.pack('>H', 14))
    # Order -> nope -> 0x00
    content.append("\x00")
    # Eternity Port
    content.append(chr(1))
    # Address
    net, subnet, universe = address
    content.append(struct.pack('<H', net << 8 | subnet << 4 | universe))
    # Length of DMX Data, High Byte First
    content.append(struct.pack('>H', len(dmxdata)))
    # DMX Data
    #print dmxdata
    for d in dmxdata:
        content.append(chr(d))
    # stitch together
    content = "".join(content)
    # debug
    # print content
    # send
    #s.sendto(content, (ip, port))