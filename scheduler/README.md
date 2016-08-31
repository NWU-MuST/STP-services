SPEECH SCHEDULER
================

The speech scheduler routine monitors a speech jobs database and manages requested or running speech jobs.

JOB FLOW
--------

A new job goes through a set number of status which are:

    * `P` - job is pending. Each new job starts in this state.
    * `D` - job is downloading data needed by the job.
    * `C` - job has finished downloading data.
    * `Q` - job is queued in GridEngine queue.
    * `R` - job is running.
    * `N` - job finished without error.
    * `F` - job failed.
    * `E` - some error occurred while trying to process the job.
    * `U` - job is uploading the result.
    * `W` - job finished uploading result.
    * `X` - job is marked for deletion.
    * `Z` - cleanup and re-submit (used by admin)


MANUALLY RUNNING THE SERVER
---------------------------

```
python scheduler.py config/scheduler.json
```

DEPENDENCIES
------------

__NOTE__: Assume Ubuntu 14.04/16.04

### GridEngine - single PC install

https://scidom.wordpress.com/2012/01/18/sge-on-single-pc/

http://www.socher.org/index.php/Main/HowToInstallSunGridEngineOnUbuntu

### Fonts

http://webappl.blogspot.co.za/2011/05/install-sun-grid-engine-sge-on-ubuntu.html

```
apt-get install xfs
service xfs start
apt-get install xfonts-75dpi
xset +fp /usr/share/fonts/X11/75dpi
xset fp rehash
```

### Python GridEngine

```
apt-get install python-drmaa gridengine-drmaa-dev gridengine-drmaa1.0
```

### Move Docker location

```
$ service docker stop
$ mkdir /home/docker
$ mv /var/lib/docker/* /home/docker
```

Add "-g /home/docker" to /etc/defaults/docker DOCKER_OPTS=""

```
$ service docker start
```

