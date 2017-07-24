# SGE submission scripts

The scripts in this directory are submitted to the SGE queue when a speech service is requested. The scripts are wrappers for the `docker`  services. See `docker/README.md` for docker service installation. The scripts names should be added to the speech services database. See `../../speech_server/tools/README.md` on how to add speech services.

## Services

The following services are available when the system is installed.

```
 * align.sh - basic alignment
 * align_html.sh - CKEditor alignment
 * diarize.sh - basic silence/non-silence diarization
 * diarize_html.sh - CKEditor silence/non-silence diarization
 * diarize_long.sh - Experimental diarization with speaker clustering
 * recognize.sh - basic speech recognition
 * recognize_html.sh - CKEditor speech recognition
```


