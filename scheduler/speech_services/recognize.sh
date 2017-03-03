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
SYSLM=`python $WHERE/json_parse.py $TICKET subsystem`

SYSTEM=`echo $SYSLM | awk -F'::' {'print $1'}`
GRAPH=`echo $SYSLM | awk -F'::' {'print $2'}`

#TODO: Check if $SYSTEM exist
docker exec -t services /home/dac/recognize/speech2text.sh --plp-config /mnt/stp/recognize/$SYSTEM/conf/plp.conf --source-dir /mnt/stp/recognize/$SYSTEM/ --graph-dir /mnt/stp/recognize/$SYSTEM/graphs/$GRAPH $AUDIO $RESULT

