#!/bin/bash

echo $1

echo "0.0 10.0" > $1.result
echo "10.0 20.0" >> $1.result
echo "20.0 30.0" >> $1.result
