# Sun Grid Engine

The job scheduler makes use of the Sun Grid Engine to queue requested jobs.
This document describes the installation and configuration of the Sun Grid Engine for a single machine, host and worker is the same machine, on Ubuntu 16.xx.

## Installation

All the installation commands should be run as root. Change in to root interactive mode:
```bash
$ sudo -i
```

### Configuration

Clear the APT packages and update the repository:
```bash
$ apt-get clean all && apt-get update
```

Install the SGE gridengine packages:
```bash
$ apt-get install gridengine-master gridengine-client gridengine-common gridengine-exec
```

During installtion you'll get the following prompts:

 * **Postfix Configuration** -- select `Local only` and set system mail name to your domain name or for example `mydomain.org`
 * **Configuring gridengine-common** -- for *Configure SGE automatically:* select `yes`
 * **Configuring gridengine-common** -- the *SGE Cell name:* can be left as `default`
 * **Configuring gridengine-client** -- set *SGE master hostname:* to `localhost`

After installation, if the SGE gridengine-master service is not running then start the service:
```bash
$ service gridengine-master restart
```
To check for the gridengine-master service run the following (check for `sge_master` process):
```bash
$ ps axf
 1072 ?        Sl     0:00 /usr/lib/gridengine/sge_qmaster
```

### Setup the qmaster

For the following steps we assume that you are configuring for a user on the host system named `stp`.

Add `stp` to the managers list:
```bash
$ qconf -am stp
```

Add `stp` to the operators list:
```bash
$ qconf -ao stp
```

Add a new scheduler configuration:
```bash
$ qconf -Msconf sge_config/grid
```
You can edit `sge_config/grid` if you understand what is going on!

Add a new host group:
```bash
$ qconf -Ahgrp hostlist 
```

Add a new queue:
```bash
$ qconf -Aq queue
```

Add the administration and submit host:
```bash
$ qconf -as localhost
$ qconf -ah localhost
```

### Setup the execd

Add a new exec host:
```bash
$ qconf -Ae hostexec
```

Add to a list attribute of an object:
```bash
$ qconf -aattr hostgroup hostlist localhost @allhosts
```

Enable the queue:
```bash
$ qmod -e speech.q@localhost
```

### Fix the hosts

Edit `/etc/hosts` file and make the following edits.
Change:
```
127.0.0.1   localhost
```
to
```
127.0.0.1   localhost   hostname
```
where `hostname` is your host system's host name.

### Restart the services
Run the following commands to restart the gridengine services:

```bash
$ service gridengine-master restart
$ service gridengine-exec restart
```

You should see the following processes running:
```bash
$ ps axf
 1072 ?        Sl     0:00 /usr/lib/gridengine/sge_qmaster
 4177 ?        Sl     0:00 /usr/lib/gridengine/sge_execd
```

To view the defined hosts and processing queue run the following commands:
```bash
$ qhost
$ qconf -sq speech.q
```

### Change the number of processing slots

To change the number of processing slots you can run the following command:
```bash
qconf -aattr queue slots "[localhost=30]" speech.q
```
This will set the number of processing slots to `30`.


## Testing

As root, add a new user named `stp`:
```bash
adduser --home /home/stp stp
```

Login as user `stp` and create the a file `tmp.sh` with this content:
```
#!/bin/bash

sleep 20
```

Submit a SGE job using:
```bash
$ qsub tmp.sh
```

To view the job use
```bash
$ qstat
```
