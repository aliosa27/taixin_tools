# taixin_tool
a web gui for taixin based halow devices

this is just a python wrapper for hgpriv
 it expects that hgpriv is installed in /sbin

 It exposes all of the get and set commands that hgpriv supports. in additon, it will create the /etc/hgicf.conf file which 
 the driver loads on load. 

theres a bunch of other stuff here, there is an rssi graph which was the reason i started this in the first place, when testing out the usb based modules.
