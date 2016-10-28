#!/bin/bash

#$ -N JOB_NAME
#$ -e ERR_OUT
#$ -o STD_OUT
#$ -cwd

TICKET=##INSTANCE_TICKET##
SPEECH_SERVICES=##SPEECH_SERVICES##

RESULTFILE=`python $SPEECH_SERVICES/json_parse.py $TICKET resultfile`
echo "Hello World" > $RESULTFILE

sleep 3

