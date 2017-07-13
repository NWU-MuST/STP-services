BUILDING AN SPEECH SERVER DOCKER IMAGE
===========================================

This directory contains the files necessary to build an speech server Docker image. To build, place the `Dockerfile` and complete repository in a build location with structure as follows:

```
.
|-- Dockerfile
|-- tech_services
`---|
    |-- install
    |-- scheduler
    |   |-- config
    |   |-- core
    |   |-- documents
    |   |-- speech_services
    |   |-- tmp
    |   `-- tools
    `-- speech_server
        |-- config
        |-- ideas
        |-- service
        |-- tools
        `-- web_admin
```

To build the docker image you must provide the user (UID) and group (GID) ids. To retrieve the UID and GID, type `id` in the Linux command line:
```bash
id
```
You will get an output that looks something like this:
```
uid=1024(ntkleynhans) gid=1027(ntkleynhans) groups=1027(ntkleynhans),4(adm),20(dialout),24(cdrom)
```

To build the docker image run, with your UID and GID (below is just an example!):

```bash
docker build -t speech --build-arg UID=1024 --build-arg GID=1027 .
```

Testing the built service
-------------------------

### Create databases

Firstly, create a directory on the host filesystem to serve as persistent file storage location (we will use `~/stp` as an example):

```bash
mkdir ~/stp
```

Use the database creation tools in `./speech_server/tools/` to create the various databases.
Setup authentication databases using `./speech_server/tools/authdb.py`.
We assume that the user is creating these databases in `~/stp`.

```
$ ./speech_server/tools/authdb.py ROOT_PASSWORD ~/stp/speech_admin.db
$ ./speech_server/tools/authdb.py ROOT_PASSWORD ~/stp/speech_auth.db
```
Setup services databases using `./speech_server/tools/servicedb.py`

```
$ ./speech_server/tools/servicedb.py ~/stp/speech_services.db
```

Setup jobs databases using `./speech_server/tools/jobsdb.py`

```
$ ./speech_server/tools/jobsdb.py ~/stp/speech_jobs.db
```

## Add a speech user

To add a user to the speech server use the following command:

```bash
$ ./speech_server/tools/adduser.py ~/stp/speech_auth.db USERNAME PASSWORD
```

You must add this `USERNAME` and `PASSWORD` to the configuration file `app_server/config/dispatcher.conf` located in the application server Git reposistory clone directory.
Edit USERNAME and PASSWORD in the JSON configuration file:
```
   "speechserver" : {
        "username" : "USERNAME",
        "password" : "PASSWORD",
        "login" : "jobs/login",
        "logout" : "jobs/logout",
        "logout2": "jobs/logout2",
        "discover" : "jobs/discover"
    }
```

### Fix Host Apache configuration

Enable Apache Proxy modules:
```bash
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod proxy_balancer
sudo a2enmod lbmethod_byrequests
```

Edit the hosts Apache configuration file (/etc/apache2/apache.conf) and add the following `ProxyPass` commands:
```
ProxyPass "/speech" "http://127.0.0.1:9950/wsgi"
ProxyPassReverse "/speech" "http://127.0.0.1:9950/wsgi"
```

If your system has a firewall then you should open the port `9950`.
See `Google search ufw open ports` or `man ufw` on how to open ports.

Restart the Apache service:
```bash
sudo service apache2 restart
```

### Run application server docker images

Run the docker image making sure:
 
  - to mount the host directory created above
  - and designate a host port for usage (`9950` in this case)
  - provide UID and GID (as in when you built the `speech` docker image above)

```bash
docker run --name speech --env UID=1024 --env GID=1027 --env SO_SNDTIMEO=600 -v /mnt/data2/home2/ntkleynhans/stp:/mnt/stp -d -p 9950:80 speech:latest
```

### Test the application server using CURL

Log into the _speech admin_ service as root:

```bash
curl -i -k -v -H "Content-Type: application/json" -X POST -d '{"username": "root", "password": ROOT_PASSWORD}' http://127.0.0.1/speech/admin/login
```

which should return a token (your token will be different and you must keep track of this token as subsquent requests make use of this token), e.g.:

```json
{"message": "YmVkNWEyNzYtM2IwZS00ZDFmLTg0YjAtYzk0YjU3ZjI2N2I1"}
```

Log into the _speech_ service as normal user:

```bash
curl -i -k -v -H "Content-Type: application/json" -X POST -d '{"username": USERNAME, "password": PASSWORD}' http://127.0.0.1/speech/login
```

Perform a user logout (assuming above command returned token = ZWJiNTU4ZGItODJkMC00MTRhLWE2ZTktYjk4N2E3MDBlMjVh):

```bash
curl -i -k -v -H "Content-Type: application/json" -X POST -d '{"token": "ZWJiNTU4ZGItODJkMC00MTRhLWE2ZTktYjk4N2E3MDBlMjVh"}' http://127.0.0.1/speech/logout
```

### Stop and remove the docker image

To stop and remove the docker container run the following:
```bash
docker stop speech
docker rm speech
```
