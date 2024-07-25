# taixin_tool
a web gui for taixin based halow devices

this is just a python wrapper for hgpriv, I will modify it to support running at commands directly so it can be ported to an esp32 

 it expects that hgpriv is installed in /sbin
 it also expects that you have copied the config files over to /etc
 it allllso expects that you leave the interface at its default name of hg0(will change this in the future)

 By default the driver loads /etc/hgcif.conf when loaded. You will need to make sure you load the driver on boot
 

 It exposes all of the get and set commands that hgpriv supports. in additon, it will create the /etc/hgicf.conf file which 
 the driver loads on load. 

 It supports upgrading firmware via the ota interface the driver exposes. 
 

theres a bunch of other stuff here, there is an rssi graph which was the reason i started this in the first place, when testing out the usb based modules.

copy the configs in etc to etc on your host. 


python server.py 
and you should be good to go!
