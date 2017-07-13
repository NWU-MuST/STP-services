# Speech Server Tools

The tools in this directory are used to:

 * Create databases
 * Utilities to add users and manage services
 * Testing the speech server

## Databases

### Authentication

The speech server requires two authenication databases: (1) admin and (2) normal users.
In the below examples we assume `~/stp/` is the host storage location for the databases.
 
Create an admin database:
```bash
$ python authdb.py ~/stp/speech_admin.db ROOT_PASSWORD
```

Create a normal users database:
```bash
$ python authdb.py ~/stp/speech_auth.db ROOT_PASSWORD
```

### Jobs queue

The speech server requires a job queue database to store jobs in a persistent manner.

To create a jobs queue run the following:

```bash
$ ./jobsdb.py ~/stp/speech_jobs.db
```

### Services

The speech server accesses a services database to confirm the requested service and required parameters.

To create a speech services database:

```bash
$ ./servicedb.py ~/stp/speech_services.db
```

## Utilities

### Add user

To add registered users to the speech server run the following:

```bash
$ ./adduser.py ~/stp/speech_auth.db USERNAME PASSWORD
```

### Services

Service management is provided by `service_util.py`.

```bash
./service_util.py ~/stp/speech_services.db TASK
```

Where `TASK` can be:
```
    * ADD - add a new service to the speech services database
    * DEL - remove an existing service
    * LS - list all services and subsystems currently registered
    * SUBADD - add a subsystem to an existing service
```

## Testing

To test the speech server API you can run the `jobs_tester.py`.

```bash
$ ./job_tester.py
Accessing Docker app server via: http://127.0.0.1:9950/wsgi/
Enter command (type help for list)>
```

This will launch an interactive testing application. You will have to edit the code to change the URL (`http://127.0.0.1:9950/wsgi/`). The tester
can run the following commands:

```
 * ADLIN - admin login
 * ADLOUT - admin logout
 * LOGIN - user login
 * LOGOUT - user logout
 * ADDJOB_DIARIZE - add a job
 * ADDJOB_RECOGNIZE - add a job
 * ADDJOB_ALIGN - add a job
 * DELETEJOB - delete a job
 * QUERYJOBS - query jobs
 * USERJOBS - display user's jobs
 * DISCOVER - discover the services
 * EXIT - quit
```
