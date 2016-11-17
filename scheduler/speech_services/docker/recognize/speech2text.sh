#!/bin/bash

set -e

# Final cleanup code
function cleanup {
  EXIT_STATUS=$?
  if [ "$?" -ne 0 ]; then
    echo "ERROR: $?"
  fi
  exit $EXIT_STATUS 
}
trap cleanup EXIT;

# Location within Docker
WHERE=$HOME/recognize
cd $WHERE

# Load Kaldi commands and path info
[ -f $WHERE/cmd.sh ] && . $WHERE/cmd.sh;
[ -f $WHERE/path.sh ] && . $WHERE/path.sh;

# Variables
mfcc_config=
segments=
utt2spk=
source_dir=
graph_dir=
format_ctm=

# Parse arguments
echo "$0 $@"
. $WHERE/utils/parse_options.sh || exit 1;

if [ $# -ne "2" ]; then
  echo "Usage: $0 <audio-file> <out-ctm>"
  echo "e.g.: $0 test.ogg text.ctm"
  echo "options:"
  echo "  --mfcc-config <config>     # MFCC config file"
  echo "  --segments <file>          # File containing time segments, each segment on new line; <START_TIME> <END_TIME>..."
  echo "  --source-dir <location>    # Location of model, transforms, etc"
  echo "  --graph-dir <location>     # Location of decoding graphs"
  echo "  --format-ctm <bool>"
  exit 1
fi

audio_file=$1
out_ctm=$2
ogg_file=$1

# Create workspace
echo "Creating workspace"
scratch=`mktemp -p . -d`
scratch=`readlink -f $scratch`
echo $scratch

# Decode OGG file
echo "Decoding ogg: $audio_file"
oggdec -o $scratch/audio.wav $audio_file || ( echo "ERROR: oggdec failed!"; exit 2 )

# Determine number of channels
channels=`soxi $scratch/audio.wav | grep 'Channels' | awk -F ':' {'print $2'} | tr -d ' '`
if [ $channels -gt "1" ]; then
  echo "ERROR: Single channel audio supported only!"
  exit 2
fi

# Fix sampling rate if needed
workname=`basename $audio_file`
base=`echo $workname | awk -F '.' {'$NF="";print $0'} | tr ' ' '.' | sed 's:\.$::g'`

# Determine audio sample rate
samprate=`soxi $scratch/audio.wav | grep 'Sample Rate' | awk -F ':' {'print $2'} | tr -d ' '`

# Determine model sample rate
modelrate=`basename $source_dir | awk -F '_' {'print $NF'}`

if [ "$modelrate" != "$samprate" ]; then
  echo "WARNING: Audio and model sample rate mismatch: AM= $modelrate, AU= $samprate"
fi

# Resample
sox $scratch/audio.wav -t wav "$scratch/$base"."wav" rate $modelrate || ( echo "ERROR: sox rate conversion failed!"; exit 2 )
audio_file="$scratch/$base"."wav"

# Create segments file; assume blank text
# Prepare data
echo "Preparing data"
diapath="$scratch/diarizer"
datadir="$scratch/data"
expdir="$scratch/exp"
mfccdir="$scratch/mfcc"
mkdir -p $diapath $mfccdir $datadir $expdir

audfp=`readlink -f $audio_file`
echo "A $audfp" > $datadir/wav.scp

# Missing segments input
if [ -z $segments ]; then
  # No segments info
  # Check the duration
  dur=`python -c "import wave; import sys; f = wave.open(sys.argv[1],'r');print (float(f.getnframes())/float(f.getframerate())); f.close()" $audio_file`
  idur=`printf '%.0f' $dur`
  if [ $idur -lt 10 ]; then
    # Less than a minute
    fdur=`python -c "import sys; print '%06d' % (100.0 * float(sys.argv[1]))" $dur`
    echo "A_000000_${fdur} A 0.0 $dur" > $datadir/segments
    echo "A_000000_${fdur} A" > $datadir/utt2spk
  else
    # Run the diarize
    DIAHOME=`dirname $WHERE`
    $DIAHOME/diarize/diarize.sh $ogg_file $datadir/diarize.ctm
    cat $datadir/diarize.ctm | awk {'print $1" A "$3" "$4'} > $datadir/segments
    $WHERE/ctm_utt2spk.py $datadir/segments $datadir/utt2spk
  fi
else
  # Convert basic segments to Kaldi segments
  while read line; do
    start=`printf "%.2f" $(echo $line | awk {'print $1'})`
    final=`printf "%.2f" $(echo $line | awk {'print $2'})`
    str_start=`printf "%06d" $(printf "%.0f" $(echo "${start}*100" | bc -l))`
    str_final=`printf "%06d" $(printf "%.0f" $(echo "${final}*100" | bc -l))`
    echo "A_${str_start}_${str_final} A $start $final"  >> $datadir/segments
  done < $segments

  $WHERE/ctm_utt2spk.py $datadir/segments $datadir/utt2spk
fi

$WHERE/utils/utt2spk_to_spk2utt.pl $datadir/utt2spk > $datadir/spk2utt || ( echo "ERROR: utt2spk to spk2utt failed!"; exit 2 )
$WHERE/utils/fix_data_dir.sh $datadir || ( echo "ERROR: Data fixing failed!"; exit 2 )
$WHERE/utils/validate_data_dir.sh --no-feats --no-text $datadir || ( echo "ERROR: Data validate failed!"; exit 2 )

# Extract MFCCs
echo "Extracting MFCCs"
$WHERE/steps/make_mfcc.sh --mfcc-config $mfcc_config --cmd "$train_cmd" --nj 1 $datadir/ $expdir/make_mfcc/ $mfccdir || ( echo "ERROR: mfcc extraction failed!"; exit 2 )

# Compute CMVN stats
echo "Computing CMVN stats"
$WHERE/steps/compute_cmvn_stats.sh $datadir $expdir/exp/make_mfcc $mfccdir || ( echo "ERROR: CMVN failed!"; exit 2 )

# Generate LDA and fMLLR transforms
echo "Computing LDA and fMLLR transforms"
$WHERE/decode_fmllr_extra_must.sh --nj 1 --cmd "$decode_cmd" --source-dir $source_dir/tri5 $source_dir/tri5/graphs $datadir $expdir/tri5/decode || ( echo "ERROR: Transform estimation failed!"; exit 2 )

echo "Performing sgmm2 decode"
$WHERE/decode_sgmm2_must.sh --nj 1 --cmd "$decode_cmd" --use-fmllr true --source-dir $source_dir/sgmm5 --transform-dir $expdir/tri5/decode $source_dir/sgmm5/graphs $datadir $expdir/sgmm5/decode || ( echo "ERROR: SGMM decode failed!"; exit 2 )

echo "Performing sgmm2 rescoring"
$WHERE/decode_sgmm2_rescore_must.sh --cmd "$decode_cmd" --source-dir $source_dir/sgmm5_mmi_b0.1 --transform-dir $expdir/tri5/decode $source_dir/sgmm5/graphs $datadir $expdir/sgmm5/decode $expdir/sgmm5_mmi_b0.1/decode || ( echo "ERROR: SGMM re-scoring failed!"; exit 2 )

# Generate CTM
echo "Lattice to CTM"
$WHERE/get_ctm_conf_must.sh --use-segments true --model $source_dir/sgmm5_mmi_b0.1/final.mdl $datadir/data-fmllr-tri3 $source_dir/sgmm5/graphs $expdir/sgmm5_mmi_b0.1/decode || ( echo "ERROR: CTM extraction!"; exit 2 )

cp $expdir/sgmm5_mmi_b0.1/decode/score/data-fmllr-tri3.ctm $out_ctm 

# Clean up
rm -fr $scratch || ( echo "ERROR: Job cleanup failed!"; exit 2 )

