# Docker services

The docker build scripts contained in this directory, should be used to build the speech services docker containers.

## Setup

### Copy Kaldi source

Copy the `Kaldi.tbz2` archive to the same location as the `docker-services` directory.

### Build the docker container

Build a the docker services by running the following command:

```bash
$ docker build -t services --build-arg UID=1000 --build-arg GID=1000 -f docker-services .
```

If you would like to build separate docker containers then replace the `docker-services` build script with `docker-align`, `docker-diarize` or `docker-recognize` build scripts.

### Run the docker container

To run the newly built docker service:

```bash
$ docker run -u dac --name services -v ~/stp:/mnt/stp -dt services:latest /bin/bash
```
Here we assume `~/stp` is where the speech resources will be placed.

To stop and remove the running instance:
```bash
$ docker stop services && docker rm services
```

### Copy resources in place

Lastly, the alignment and recognition resources should be copied and extracted to `~/stp`.

Extract alignment and recognition:
```bash
$ cp align.tbz2 && cd ~/stp/ && tar -xjf align.tbz2
$ cp recognize.tbz2 && cd ~/stp/ && tar -xjf recognize.tbz2
```
