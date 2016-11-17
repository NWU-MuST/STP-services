#!/bin/bash

#$ -N ##JOB_NAME##
#$ -e ##ERR_OUT##
#$ -o ##STD_OUT##
#$ -cwd

TICKET=##INSTANCE_TICKET##
WHERE=##SPEECH_SERVICES##
DOCKER_PATH=##DOCKER_PATH##
REAL_PATH=##REAL_PATH##

AUDIO=`python $WHERE/json_parse.py $TICKET audiofile | sed "s:"$REAL_PATH":"$DOCKER_PATH":g"`
RESULT=`python $WHERE/json_parse.py $TICKET resultfile | sed "s:"$REAL_PATH":"$DOCKER_PATH":g"`
SYSTEM=`python $WHERE/json_parse.py $TICKET subsystem`

#TODO: Check if $SYSTEM exist
docker exec -t services /home/dac/recognize/speech2text.sh --mfcc-config /mnt/stp/recognize/$SYSTEM/conf/mfcc.conf --source-dir /mnt/stp/recognize/$SYSTEM/ --graph-dir /mnt/stp/recognize/$SYSTEM/tri5/graphs/ $AUDIO $RESULT

