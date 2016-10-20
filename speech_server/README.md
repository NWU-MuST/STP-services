SPEECH SERVER
=============

Web service that manages speech jobs.

MANUALLY RUNNING THE SERVER
---------------------------

Example of how to run the server (Apache2 + uWSGI):

```bash
/usr/sbin/apache2ctl start & uwsgi --uid 1000 -l 2 -p 1 --master --enable-threads --plugin /usr/lib/uwsgi/plugins/python27_plugin.so --socket 127.0.0.1:9090 --wsgi-file wsgi.py  --env services_config=config/dispatcher.json

API:
----

### LOGIN

Login with username and password. You must be a registered user.
A token will be generated and sent back in the response.

```
/wsgi/login

JSON request data: { username : "username", password : "password" }

JSON response data: { token : "token" }

```

### LOGOUT

Logout using token.

```
/wsgi/logout

JSON request data: { token : "token" }

```

### ADD JOB

Add speech job to queue.

```
/wsgi/addjob

JSON request data: { token : "token", service : "service", subsystem : "subsystem", getaudio : "getaudio", postresults : "postresult"}

For alignment gettext should be added to request data: { gettext : "gettext" }

JSON response data: { jobid : "jobid" }

```

__NOTE__: *postresult*, *getaudio* and *gettext* urls should be network accessible.
When the speech job runs the data will be downloaded using *getaudio* and *gettext* urls.
The job result will be posted to *postresult* url.

### DELETE JOB

Mark speech job for deletion. The job is identified by the provided jobid.

```
/wsgi/deletejob

JSON request data: { token : "token" jobid : "jobid"}

```

### QUERY JOB

Query speech job information. The job is identified by the provided jobid.


```
/wsgi/queryjob

JSON request data: { token : "token", jobid : "jobid"}

JSON response data: {"subsystem": "default", "service": "diarize", "text": "N", "postresult": "http://127.0.0.1/", "token": "YTRiODM0OWUtYzQyMC00ODJkLWE3NjMtN2I3MTEyODI0M2Vk", "command": "diarize.sh", "ticket": ["j361b61de366945c59055ff93753808c0", "appserver", "/path/", "D", "", 1470816911.461316], "audio": "Y", "getaudio": "http://127.0.0.1/test.ogg"}

```

### USERS JOBS

List all jobs belonging to user.

```
/wsgi/userjobs

JSON request data: { token : "token", jobid : "jobid"}

JSON reponse data: {"jobids": ["jef6471ea820d477da00456692207cfcb", "jaa0cf8494fc6465a819a27ff27d6a1a9", "jb55e102ee95b49769a48cb0763141eda", "jcc372c392ba64a40988f3850105c11c5"] }

```

### DISCOVER

List services offered by speech server. The response will contain:
    1. *services* - services offered by speech system
    2. *subsystems* - service's subsystems 
    3.*requirements* - audio and text requirements for services
    

```
/wsgi/discover

JSON request data: { token : "token"}

JSON reponse data: {"services": ["diarize", "recognize", "align"], "subsystems": {"diarize": [{"subsystem": "default"}], "align": [{"subsystem": "en-ZA"}], "recognize": [{"subsystem": "en-ZA"}]}, "requirements": [{"text": "N", "audio": "Y", "name": "diarize"}, {"text": "N", "audio": "Y", "name": "recognize"}, {"text": "Y", "audio": "Y", "name": "align"}]}
```

