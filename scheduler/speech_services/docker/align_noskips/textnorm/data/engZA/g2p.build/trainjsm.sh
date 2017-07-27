#!/bin/bash
set -e

SEQUITUR=g2p.py
JSMG2P_N=6

workdir=$PWD

for indict in saeng_oald.20170112; do
    #Simple dict to JSModel
    $SEQUITUR -e UTF8 --train ${indict}.txt --devel 5% --write-model $workdir/${indict}_jsm-1.pickle
    for i in `seq 2 $JSMG2P_N`; do
	prevmodel=$workdir/${indict}_jsm-`expr $i - 1`.pickle
	nextmodel=$workdir/${indict}_jsm-${i}.pickle
	$SEQUITUR -e UTF8 --model $prevmodel --ramp-up --train ${indict}.txt --devel 5% --write-model $nextmodel
    done
done
