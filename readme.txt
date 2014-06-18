==== ArtemisProxy.py ====

A man in the middle proxy for the Artemis Space Bridge Simulator (http://www.artemis.eochu.com/). Pipes events from the game to an ArtNet Node to allow special effects to be triggered or for new visual displays to be added.

Usage:
ArtemisProxy : proxy between Artemis clients and server, forwards certain events to an ArtNet Node
       [-h] --serverip SERVERIP --listenip LISTENIP
       [--artnetserverip ARTNETSERVERIP] --sntfile SNTFILE

optional arguments:
  -h, --help            				Show this help message and exit
  --serverip SERVERIP   				Artemis server IP
  --listenip LISTENIP   				IP to listen for clients on
  --artnetserverip ARTNETSERVERIP		ArtNet Node IP
  --sntfile SNTFILE     				.snt file of ship being used

Example:
"c:\Program Files\Python27\python.exe" "c:\Users\Artemis\Desktop\Artemis Python\ArtNetArtemis\ArtemisProxy.py" --serverip 192.168.0.127 --listenip 192.168.0.135 --artnetserverip 192.168.0.137 --sntfile "C:\Program Files\Artemis2\dat\artemis.snt"


The .snt file for the ship being used in the sim. Its found in the "dat" folder of the Artemis installation. Its used to map ship damage to subsytem names. To figure out which one to use check "Vesseldata.xml"


Start this tool on a client machine with serverip set to the Artemis server ip and listenip set to the local IP of the machine. 
Then start the Artemis client and connect to the local IP, it should connect normally and the tool should start showing data passing through.

Make sure that the client is set to use the "engineering" station or you dont get the full set of stats out of the tool

