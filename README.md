# taixin tools
a web gui and other tools for taixin based halow devices

Theres a python implementation of libnetat which I keep in sync with
my updated c version of libnetat with lots of quality of life fixes. 

they both support the same things.

features: both interactive and non interactive modes so you can script againt them.
exit command in interactive mode.
scan command in both modes.
setmac command in interactive mode.

libnetat/.py interfacename for interactive mode
libnetat/.py interfacename scan - returns mac addresses of devices
libnetat/.py interfacename at+command 00:00:00:00:06:33 - send command to dst mac on the interface specified. 

to switch devices in interactive mode, run scan or setmac. it will default to the first device it detects. you can run showmac to verify your connected to the right device 

theres a python implementation of hgpriv as well but currently it can only set things

server.py is a python web based wrapper for hgpriv with basic support for libnetat.

 it expects that hgpriv or libnetat are compiled and installed in /sbin.
 The mode can be switched in /etc/mode.conf or via the web gui on the system page.

You will need to compile my version of libnetat, it adds support to run at commands from the command line, device switching, scanning, and supports running commands on remote devices by passing a mac address on the command line. 

libnetat support is basic, rssi/connection status/etc work. 
 site survey does not work in this mode yet but that seems to be a firmware issue.
 
 sever.py expects that you have copied the config files over to /etc
 it also expects that you leave the interface at its default name of hg0(will change this in the future)

By default the driver loads /etc/hgcif.conf when loaded. You will need to make sure you load the driver on boot
 

 It exposes all of the get and set commands that hgpriv supports. in additon, it will create the /etc/hgicf.conf file which 
 the driver loads on load. 

 It supports upgrading firmware via the ota interface the driver exposes. 
 

theres a bunch of other stuff here, there is an rssi graph which was the reason i started this in the first place, when testing out the usb based modules.

copy the configs in etc to etc on your host. 


python server.py 
and you should be good to go!
