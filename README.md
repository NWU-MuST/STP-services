Language Technology Services for Speech Transcription Platform
==============================================================

This is the Language Technology Services component implemented for the Speech Transcription Platform project by the [Multilingual Speech Technologies](http://www.nwu.ac.za/must/) group at North-West University. The project was sponsored by the Department of Arts and Culture of South Africa.

The speech services module is broken up into two parts:
    1. Speech Server
    2. Scheduler

Below are the basic installation instructions for __this component__, however, documentation for the project/platform as a whole can be found [here](https://bitbucket.org/ntkleynhans/stp_docs), refer specifically to the [Master Installation Document](https://bitbucket.org/ntkleynhans/stp_docs/raw/e2cf012def8a2a1aa1ebd132f826bff95e361592/installation/Master_Installation.pdf).

This repository contains software developed by third parties under their respective licences. For specific licence conditions please refer to the documentation contained in the relevant sub-directory or source code file.

## Speech Server

Web interface where speech jobs are managed. See `./speech_server/README.md`

## Scheduler

Service that regularly inspects the speech service database to manage requested speech jobs. See `./scheduler/README.md`

## Setup

Assuming Ubuntu 14.04/16.04:

### Clone source

Clone the speech server from BitBucket https://bitbucket.org/ntkleynhans/tech_services.git

```bash
$ sudo apt-get install git python-bcrypt
$ git clone https://bitbucket.org/ntkleynhans/tech_services.git tech_services
$ ln -s tech_services/install/Dockerfile
```

### Install Docker

Next step is to install Docker:
```bash
$ sudo apt-get install docker.io
```

Add yourself to the docker group:
```bash
$ sudo gpasswd -a <your_user_name> docker
```

Log out and log in for group change to take effect


**Change docker location (optional)**

Change docker image location.

Stop docker service:
```bash
sudo service docker stop
```

Edit /etc/defaults/docker file and add the following option:
```bash
DOCKER_OPTS="-g /home/docker"
```

Create new docker location:
```bash
sudo mkdir /home/docker
```

Restart the docker service:
```bash
sudo service docker start
```

### Create databases

Use the database creation tools in `./speech_server/tools/` to create the various databases.  

Setup authentication databases using `./speech_server/tools/authdb.py`. We assume that the user is creating these databases in `~/stp`.

```bash
$ mkdir ~/stp
$ ./speech_server/tools/authdb.py ~/stp/speech_admin.db ROOT_PASSWORD
$ ./speech_server/tools/authdb.py ~/stp/speech_auth.db ROOT_PASSWORD
```

Setup services databases using `./speech_server/tools/servicedb.py`

```bash
$ ./speech_server/tools/servicedb.py ~/stp/speech_services.db
```

Setup jobs databases using `./speech_server/tools/jobsdb.py`

```bash
$ ./speech_server/tools/jobsdb.py ~/stp/speech_jobs.db
```

### Build speech server docker image

Build the application server Docker image. For more instructions see `./install/README.md`

### Services

Copy services' resources inplace, setup services database and build services docker image. For more information see `./scheduler/README.md`
