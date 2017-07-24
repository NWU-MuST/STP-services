# SPEECH SCHEDULER

The speech scheduler routine monitors a speech jobs database and manages requested or running speech jobs.

## JOB FLOW


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

## DEPENDENCIES

You must perform the following before launching the scheduler.

### Sun GridEngine

Install Sun GridEngine and configure.
See ./tools/README.md

### Build Services Docker Image

Build and run the services `docker`.
See ./speech_services/docker/README.md

## MANUALLY RUNNING THE SCHEDULER

### Edit scheduler configuration

Make sure the `jobsdb`, `services` and `storage` variables point to the correct location.
Edit the JSON configuration.

Example:
```
    "jobsdb": "/home/ntkleynhans/stp/speech_jobs.db",
    "services": "/home/ntkleynhans/workspace/gitprojects/tech_services/scheduler/speech_services",
    "storage": "/home/ntkleynhans/stp/jobs/",
```

### Launch the scheduler

You must start the scheduler on the host system to routinely monitor the speech queue.
We would suggest launching a `tmux` session before starting the scheduler.

```bash
$ python scheduler.py config/scheduler.json
```
