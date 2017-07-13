#Language technology services

The speech services module is broken up into two parts:
    1. Speech Server
    2. Scheduler

##Speech Server

Web interface where speech jobs are managed.
See `./speech_server/README.md`

##Scheduler

Service that regularly inspects the speech service database to manage requested speech jobs.
See `./scheduler/README.md`

##Setup

Assuming Ubuntu 14.04/16.04:

### Clone source

Cloned speech server from BitBucket [https://bitbucket.org/ntkleynhans/tech_services.git](https://bitbucket.org/ntkleynhans/tech_services.git)

```
$ sudo apt-get install git python-bcrypt
$ mkdir work
$ cd work
$ git clone https://bitbucket.org/ntkleynhans/tech_services.git tech_services
$ ln -s tech_services/install/Dockerfile
```

### Docker installation
Next step is to install Docker:
```
$ sudo apt-get install docker.io
```

Add yourself to the docker group:
```
$ sudo gpasswd -a <your_user_name> docker
```

Log out and log in for group change to take effect


**Change docker location (optional)**

Change docker image location.

Stop docker service:
```
sudo service docker stop
```

Edit /etc/defaults/docker file and add the following option:
```
DOCKER_OPTS="-g /home/docker"
```

Create new docker location:
```
sudo mkdir /home/docker
```

Restart the docker service:
```
sudo service docker start
```

### Create databases

Use the database creation tools in `./speech_server/tools/` to create the various databases.  

Setup authentication databases using `./speech_server/tools/authdb.py`.
We assume that the user is creating these databases in `~/stp`.

```
$ mkdir ~/stp
$ ./speech_server/tools/authdb.py ROOT_PASSWORD ~/stp/speech_admin.db
$ ./speech_server/tools/authdb.py ROOT_PASSWORD ~/stp/speech_auth.db
```
Setup services databases using `./speech_server/tools/servicedb.py`

```
$ mkdir -p ~/stp/
$ ./speech_server/tools/servicedb.py ~/stp/speech_services.db
```

Setup jobs databases using `./speech_server/tools/jobsdb.py`

```
$ mkdir -p ~/stp/
$ ./speech_server/tools/jobsdb.py ~/stp/speech_jobs.db
```

### Build speech server docker image

Build the application server Docker image.
For more instructions see `./install/README.md`


### Services

Copy services' resources inplace, setup services database and build services docker image.
For for information see `./scheduler/README.md`
