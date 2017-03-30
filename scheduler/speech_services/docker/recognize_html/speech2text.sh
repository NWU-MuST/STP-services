#!/bin/bash

set -e
scratch=""

# Final cleanup code
#function cleanup {
#  EXIT_STATUS=$?
#  if [ "$?" -ne 0 ]; then
#    echo "ERROR: $?"
#  fi
#  rm -rf $scratch
#  exit $EXIT_STATUS 
#}
#trap cleanup EXIT;

# Location within Docker
WHERE=$HOME/recognize_html
cd $WHERE

# Load Kaldi commands and path info
[ -f $WHERE/cmd.sh ] && . $WHERE/cmd.sh;
[ -f $WHERE/path.sh ] && . $WHERE/path.sh;

# Variables
#mfcc_config=
plp_config=
utt2spk=
source_dir=
graph_dir=
rec_len=360

# Parse arguments
echo "$0 $@"
. $WHERE/utils/parse_options.sh || exit 1;

if [ $# -ne "3" ]; then
  echo "Usage: $0 <audio-file> <in-html> <out-html>"
  echo "e.g.: $0 test.ogg in.html out.html"
  echo "options:"
  #echo "  --mfcc-config <config>     # MFCC config file"
  echo "  --plp-config <config>      # PLP config file"
  echo "  --source-dir <location>    # Location of model, transforms, etc"
  echo "  --graph-dir <location>     # Location of decoding graphs"
  echo "  --rec-len <float>          # Maximum decoding length"
  exit 1
fi
echo "$0 $@"
audio_file=$1
ogg_file=$1
in_html=$2
out_html=$3

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
sox $scratch/audio.wav -t wav "$scratch/$base"."wav" rate $modelrate || ( echo "ERROR: sox rate conversion failed!" 1>&2; exit 2 )
audio_file="$scratch/$base"."wav"

# Create segments file; assume blank text
# Prepare data
echo "Preparing data"
diapath="$scratch/diarizer"
datadir="$scratch/data"
expdir="$scratch/exp"
#mfccdir="$scratch/mfcc"
#mkdir -p $diapath $mfccdir $datadir $expdir
plpdir="$scratch/plp"
mkdir -p $diapath $plpdir $datadir $expdir

audfp=`readlink -f $audio_file`
echo "A $audfp" > $datadir/wav.scp
seg_file="$scratch/seg"
inter_file="$scratch/inter"

$WHERE/extract_html_segments.py $audio_file $in_html $seg_file $inter_file $rec_len
# Convert basic segments to Kaldi segments
while read line; do
  tag=`echo $line | awk {'print $1'}`
  if [ "$tag" != "sil" ]; then
    start=`printf "%.2f" $(echo $line | awk {'print $2'})`
    final=`printf "%.2f" $(echo $line | awk {'print $3'})`
    str_start=`printf "%06d" $(printf "%.0f" $(echo "${start}*100" | bc -l))`
    str_final=`printf "%06d" $(printf "%.0f" $(echo "${final}*100" | bc -l))`
    if [ $str_start != $str_final ]; then
        echo "A-${str_start}-${str_final} A $start $final"  >> $datadir/segments
    fi
  fi
done < $seg_file

if [ ! -s $seg_file ]; then
  echo "WARNING: no segments found to recognize! Maybe remove text from segments or breakup segments!"
  cp $in_html $out_html
  rm -fr $scratch || ( echo "ERROR: Job cleanup failed!" 1>&2; exit 2 )
  exit 0
fi

$WHERE/ctm_utt2spk.py $datadir/segments $datadir/utt2spk
$WHERE/utils/utt2spk_to_spk2utt.pl $datadir/utt2spk > $datadir/spk2utt || ( echo "ERROR: utt2spk to spk2utt failed!" 1>&2; exit 2 )
$WHERE/utils/fix_data_dir.sh $datadir || ( echo "ERROR: Data fixing failed!" 1>&2; exit 2 )
$WHERE/utils/validate_data_dir.sh --no-feats --no-text $datadir || ( echo "ERROR: Data validate failed!" 1>&2; exit 2 )

# Extract MFCCs
#echo "Extracting MFCCs"
#$WHERE/steps/make_mfcc.sh --mfcc-config $mfcc_config --cmd "$train_cmd" --nj 1 $datadir/ $expdir/make_mfcc/ $mfccdir || ( echo "ERROR: mfcc extraction failed!" 1>&2; exit 2 )

# Compute CMVN stats
#echo "Computing CMVN stats"
#$WHERE/steps/compute_cmvn_stats.sh $datadir $expdir/exp/make_mfcc $mfccdir || ( echo "ERROR: CMVN failed!" 1>&2; exit 2 )

# Extract PLPs
echo "Extracting PLPs"
$WHERE/steps/make_plp.sh --plp-config $plp_config --cmd "$train_cmd" --nj 1 $datadir/ $expdir/make_plp/ $plpdir || ( echo "ERROR: PLP extraction failed!" 1>&2; exit 2 )

# Compute CMVN stats
echo "Computing CMVN stats"
$WHERE/steps/compute_cmvn_stats.sh $datadir $expdir/exp/make_plp $plpdir || ( echo "ERROR: CMVN failed!" 1>&2; exit 2 )

# Generate LDA and fMLLR transforms
echo "Computing LDA and fMLLR transforms"
$WHERE/decode_fmllr_extra_must.sh --nj 1 --cmd "$decode_cmd" --source-dir $source_dir/tri5 $graph_dir/tri5 $datadir $expdir/tri5/decode || ( echo "ERROR: Transform estimation failed!" 1>&2; exit 2 )

echo "Performing sgmm2 decode"
$WHERE/decode_sgmm2_must.sh --nj 1 --cmd "$decode_cmd" --use-fmllr true --source-dir $source_dir/sgmm5 --transform-dir $expdir/tri5/decode $graph_dir/sgmm5 $datadir $expdir/sgmm5/decode || ( echo "ERROR: SGMM decode failed!" 1>&2; exit 2 )

echo "Performing sgmm2 rescoring"
$WHERE/decode_sgmm2_rescore_must.sh --cmd "$decode_cmd" --source-dir $source_dir/sgmm5_mmi_b0.1 --transform-dir $expdir/tri5/decode $graph_dir/sgmm5 $datadir $expdir/sgmm5/decode $expdir/sgmm5_mmi_b0.1/decode || ( echo "ERROR: SGMM re-scoring failed!" 1>&2; exit 2 )

# Generate CTM
echo "Lattice to CTM"
$WHERE/get_ctm_conf_must.sh --use-segments true --model $source_dir/sgmm5_mmi_b0.1/final.mdl $datadir/data-fmllr-tri3 $graph_dir/sgmm5 $expdir/sgmm5_mmi_b0.1/decode || ( echo "ERROR: CTM extraction!" 1>&2; exit 2 )

python ctm_ckeditor_v2.py A $seg_file $inter_file $expdir/sgmm5_mmi_b0.1/decode/score/data-fmllr-tri3.ctm $out_html

# Clean up
rm -fr $scratch || ( echo "ERROR: Job cleanup failed!" 1>&2; exit 2 )

exit 0

