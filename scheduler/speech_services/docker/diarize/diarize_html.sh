#!/bin/bash

set -e

WHERE="$HOME/diarize/"
PRAATBIN="$WHERE/praat"
scratch=

# Final cleanup code
function cleanup {
  EXIT_STATUS=$?
  if [ "$?" -ne 0 ]; then
    echo "ERROR: $?"
  fi
  exit $EXIT_STATUS 
}

trap cleanup EXIT;

# Parse arguments
if [ $# -ne 2 ]; then
    echo "$0 in_audio_file out_textgrid"
    exit 1
fi

audio_file=$1
out_ctm=$2

# Create workspace
echo "Creating workspace"
scratch=`mktemp -p . -d`
scratch=`readlink -f $scratch`
echo $scratch

# Decode OGG file
echo "Decoding ogg: $audio_file"
oggdec -o $scratch/audio.wav $audio_file || ( echo "oggdec failed!"; exit 2 )

# Bandpass filter audio
echo "Sox filtering 75-1000: $scratch/audio.wav"
sox $scratch/audio.wav $scratch/vuv.wav sinc 75-1000 || ( echo "sox vuv filter failed!"; exit 2 )

# Run PRAAT V/UV classification
echo "Extracting VUV"
textgrid="$scratch/textgrid"
$PRAATBIN $WHERE/get_vuv_textgrid.praat $scratch/vuv.wav $textgrid || ( echo "praat vuv failed!"; exit 2 )

# Find segments
echo "Converting to CTM"
python $WHERE/basic_segments_html.py --threshold 0.5 $textgrid $out_ctm

echo "Done... $out_ctm"
rm -r $scratch

