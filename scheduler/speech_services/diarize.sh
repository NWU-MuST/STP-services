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
SEGMENTNO=`python $WHERE/json_parse.py $TICKET segmentno | sed "s:"$REAL_PATH":"$DOCKER_PATH":g"`

docker exec -u dac -t services /home/dac/diarize/diarize.sh $AUDIO $SEGMENTNO $RESULT

