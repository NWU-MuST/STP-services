GRIDENGINE
-----------

As root

Set $USER and add to managers:
qconf -am $USER

then operators:
qconf -ao $USER

Update Scheduler:
qconf -Msconf grid

Edit Queue:
vi hostlist
qconf -Ahgrp hostlist 

Add queue
qconf -Aq queue 

Hosts
qconf -as localhost
qconf -ah localhost

Worker:
qconf -Ae hostexec 
qconf -aattr hostgroup hostlist localhost @allhosts
qmod -e speech.q@localhost
qconf -aattr queue slots "[localhost=30]" speech.q
service gridengine-exec restart


qhost
service gridengine-master restart
vi queue

qhost
reboot
vi hostexec
qhost
qconf -sql
qconf
qconf -qs speech.q
qconf -sq speech.q

