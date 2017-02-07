GRIDENGINE
-----------

As root
qhost
service gridengine-master restart
vi hostlist
qconf -Ahgrp hostlist 
vi queue
qconf -Aq queue 
qhost
reboot
qconf -as localhost
qconf -ah localhost
vi hostexec
qconf -Ae hostexec 
qconf -aattr hostgroup hostlist localhost @allhosts
qmod -e speech.q@localhost
qconf -aattr queue slots "[localhost=30]" speech.q
qhost
qconf -sql
qconf
qconf -qs speech.q
qconf -sq speech.q

