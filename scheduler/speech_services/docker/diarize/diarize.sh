#!/bin/bash

set -e

WHERE="$HOME/diarize/"
PRAATBIN="$WHERE/praat"
scratch=

# Final cleanup code
#function cleanup {i
#  EXIT_STATUS=$?
#  if [ "$?" -ne 0 ]; then
#    echo "ERROR: $?" > 1>&2
#  fi
#  exit $EXIT_STATUS 
#}
#trap cleanup EXIT;

# Parse arguments
if [ $# -ne 3 ]; then
    echo "$0 in_audio_file dur out_textgrid"
    exit 1
fi

echo "$0 $@"
audio_file=$1
dur=$2
out_ctm=$3

# Create workspace
echo "Creating workspace"
scratch=`mktemp -p . -d`
scratch=`readlink -f $scratch`
echo $scratch

# Decode OGG file
echo "Decoding ogg: $audio_file"
oggdec -o $scratch/audio.wav $audio_file || ( echo "ERROR: oggdec failed!" 1>&2; exit 2 )

# Determine number of channels
channels=`soxi $scratch/audio.wav | grep 'Channels' | awk -F ':' {'print $2'} | tr -d ' '`
if [ $channels -gt "1" ]; then
  echo "ERROR: Single channel audio supported only!" 1>&2
  exit 2
fi

# Bandpass filter audio
echo "Sox filtering 75-1000: $scratch/audio.wav"
sox $scratch/audio.wav $scratch/vuv.wav sinc 75-1000 || ( echo "ERROR: sox vuv filter failed!" 1>&2; exit 2 )

# Run PRAAT V/UV classification
echo "Extracting VUV"
textgrid="$scratch/textgrid"
$PRAATBIN $WHERE/get_vuv_textgrid.praat $scratch/vuv.wav $textgrid || ( echo "ERROR: praat vuv failed!" 1>&2; exit 2 )

# Find segments
echo "Converting to CTM"
#python $WHERE/basic_segments_target_number.py --target $segment_no $textgrid $out_ctm || ( echo "ERROR: Basic segments creations failed!" 1>&2; exit 2 )
python $WHERE/basic_segments.py -t $dur $textgrid $out_ctm || ( echo "ERROR: Basic segments creations failed!" 1>&2; exit 2 )

echo "Done... $out_ctm"
rm -r $scratch

exit 0
