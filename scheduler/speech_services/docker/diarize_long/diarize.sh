#!/bin/bash
set -eu

# -----------------------------------------------------------------------------
# Function: remove_dir

# If a dir exists, does rm -r dir, else prints info message about non-existant
# directory

function remove_dir {
  if [ $# -ne 1 ]; then
    echo "Usage: $FUNCNAME <dir>"
    exit $E_BAD_ARGS
  fi
  dir=$1

  if [ -d $dir ]; then
    echo "INFO: Recursively removing '$dir'...";
    rm -r $dir
  else
    echo "INFO: '$dir' does not exist!"
  fi
}

# -----------------------------------------------------------------------------

# Function: safe_remove_dir
# 
# "Safe remove" because:
# - option to prompt a user before deleting a non-empty directory 
# - does not use -f (which is necessary if a directory does not exist, otherwise
#   bash script exists due to set -eu.

function safe_remove_dir {
  if [ $# -ne 2 ]; then
    echo "Usage: $FUNCNAME <dir> <1/0 (prompt/don't prompt)>"
    exit $E_BAD_ARGS
  fi

  dir=$1
  prompt_before_remove=$2

  if [ -d $dir ]; then
    if [ "$(ls -A $dir)" ]; then
       echo "Warning: '$dir' is not empty!"
       if [ $prompt_before_remove -eq 1 ]; then
         prompt_remove_dir $dir
       else
         remove_dir $dir
       fi
    else
      echo "Info: '$dir' is empty. Removing..."
      rmdir $dir
    fi
  else
    echo "Warning: '$dir' does not exist."
  fi
}

# -----------------------------------------------------------------------------

#if [ $# -ne "5" ]; then
#  echo "Usage: $0 <in:fn-wav> <par:BIC> <par:nj> <out:fn-seg> <out:dir-work>"
if [ $# -ne "5" ]; then
  #echo "usage: $0 <in:fn-wav> <par:bic> <par:nj> <out:fn-seg>"
  #echo "  fn-wav    - audio file to be segmented into speech/silence"
  echo "usage: $0 <in:fn-ogg> <par:bic> <par:nj> <par:chunksize> <out:fn-seg>"
  echo "  fn-ogg    - audio file to be segmented into speech/silence (OGG Vorbis format)"
  echo "  BIC       - 0 (don't use it) or 1 (use it)"
  echo "  nj        - number of processors available for parallelization"
  echo " chunksize  - the ideal size for segment size"
  echo "  fn-seg    - output segmentation file"
  #echo "  dir-work  - directory within which all output created"
  #echo "e.g.: $0 abc.wav 0 4 abc.seg /tmp"
  echo "e.g.: $0 abc.wav 0 4 600 abc.seg"
  exit 1;
fi

# -----------------------------------------------------------------------------
echo "$0 $@"
#dir_script="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
dir_script=/home/dac/diarize_long

ogg=$1
bic=$2
nj=$3
chunksize=$4
seg_out=$5
#dir_work=$5
dir_work=`mktemp -p . -d`
dir_work=`readlink -f $dir_work`

#safe_remove_dir $dir_work 0
#mkdir -p $dir_work

seg_dur=600 # duration in seconds = 10m00s

# -----------------------------------------------------------------------------
# SCRIPTS
# -----------------------------------------------------------------------------

blind_fixed_duration_segmentation=$dir_script/segmentation/do_blind_fixed_dur_segmentation.sh
speech_sil_segmentation=$dir_script/speech_sil_detection/do_speech_sil_detection.sh
bic_segmentation=$dir_script/diarization/do_bic_segmentation.sh
cluster=$dir_script/diarization/do_clustering.sh
process_cluster_results=$dir_script/diarization/do_post_process_cluster_results.sh
cv=$dir_script/diarization/do_cv.sh

# -----------------------------------------------------------------------------

# Check required scripts / software

binaries=( sox soxi oggdec ) 
scripts=( $blind_fixed_duration_segmentation
          $speech_sil_segmentation
	  $bic_segmentation
	  $cluster
	  $process_cluster_results )

exit_status=0
missing=""
for bin in "${binaries[@]}"; do
  type -p $bin &> /dev/null
  if [ $? -ne 0 ]; then
    missing="$missing [$bin]"
    exit_status=2
  fi
done

for script in "${scripts[@]}"; do
  if [ ! -e "$script" ]; then
    missing="$missing [$script]"
    exit_status=2
  fi
done

if [ $exit_status = 2 ]; then
  echo "Error: Binaries/scripts missing! $missing" 1>&2
  exit $exit_status
else
  echo "Info: All required software present"
fi

# -----------------------------------------------------------------------------

# Get audio file information
oggdec -o $dir_work/audio.wav $ogg || ( echo "ERROR: oggdec failed!" 1>&2; exit 2 )
wav="$dir_work/audio.wav"

bn=`echo $wav | awk -F '/' '{print $NF}' | sed "s/\.[^\.]\+$//g"` || ( echo "ERROR: basename $wav failed!" 1>&2; exit 2 )
dur=`soxi $wav | grep "Duration" | awk '{print $3}' | awk -F ':' '{print $1*60*60 + $2*60 + $3}'` || ( echo "ERROR: sox duration $wav failed!" 1>&2; exit 2 )
sf=`soxi $wav | grep "Sample Rate" | awk '{print $NF}'` || ( echo "ERROR: sox information $wav failed!" 1>&2; exit 2 )

# -----------------------------------------------------------------------------

# Split audio file into $segment_duration segments
# Questions: overlap? For now, no.

bash ${blind_fixed_duration_segmentation} ${wav} ${dir_work} ${seg_dur} || ( echo "ERROR: bash ${blind_fixed_duration_segmentation} failed!" 1>&2; exit 2 )
soxi ${dir_work}/blind_segmentation/*.wav | grep "Duration" || ( echo "ERROR: sox duration failed!" 1>&2; exit 2 )

# -----------------------------------------------------------------------------

bn_orig=$bn
wav_orig=$wav
work_orig=$dir_work

for wav in `find $dir_work/blind_segmentation -iname "*.wav"`
do
  echo "Info: Performing diarization on '$wav'"
  bn=`echo $wav | awk -F '/' '{print $NF}' | sed "s/\.[^\.]\+$//g"`
  touch $work_orig/${bn}.running
  dir_work=$work_orig/work_split_approach/${bn_orig}/${bn}
  safe_remove_dir $dir_work 0
  mkdir -p $dir_work

  (
  # SPEECH SILENCE DETECTION

  echo "Info: Speech silence segmentation"

  speech_sil_seg=$dir_work/${bn}.speech_sil.seg
  bash ${speech_sil_segmentation} ${wav} $speech_sil_seg $dir_work ${nj} || ( echo "ERROR: bash ${speech_sil_segmentation} failed!" 1>&2; exit 2 )

  # -----------------------------------------------------------------------------

  # BIC SEGMENTATION

  sbic_seg=$speech_sil_seg
  if [ $bic -eq 1 ]; then
    echo "Info: BIC segmentation"

    sbic_seg=$dir_work/${bn}.sbic.seg
    bash $bic_segmentation ${wav} ${sbic_seg} $dir_work $speech_sil_seg speech || ( echo "ERROR: bash $bic_segmentation failed!" 1>&2; exit 2 )
  else
    echo "Info: Skipping BIC segmenatation. Using speech sil segmentation for clustering."
    sbic_seg=$speech_sil_seg
  fi

  # -----------------------------------------------------------------------------

  # CLUSTERING

  echo "Info: Clustering segments to form 'speakers'"
  segments=$sbic_seg
  bash $cluster ${wav} ${segments} $bic $dir_work ${nj} || ( echo "ERROR: bash $cluster failed!" 1>&2; exit 2 )
  mv $work_orig/${bn}.running $work_orig/.${bn}.done
  ) |& tee -a $dir_work/log.txt &

  num_running=`find $work_orig -iname "*.running" | wc -l`
  while [ $num_running -ge $nj ];
  do
    sleep 2
    num_running=`find $work_orig -iname "*.running" | wc -l`
  done
done

wait

# -----------------------------------------------------------------------------

# RESCORE ORIGINAL WAV WITH ALL MODELS

dir_work=$work_orig
wav=$wav_orig
bn=$bn_orig

find $work_orig -iname "*.gmm.boost.merged.seg" |\
     sed "/re-cluster/d" > $dir_work/${bn}.gmm.boost.merged.seg.lst
find $work_orig -iname "*.speech_sil.seg" |\
     grep -P "\d+\.\d+-\d+\.\d+" |\
     sed "/re-cluster/d" > $dir_work/${bn}.speech_sil.txt

bash $process_cluster_results ${wav} \
  	                           $dir_work/${bn}.gmm.boost.merged.seg.lst \
	                           $dir_work/${bn}.speech_sil.txt \
                                   $dir_work || ( echo "ERROR: bash $process_cluster_results failed!" 1>&2; exit 2 )

bash ${cv} ${wav} $dir_work/${bn}.gmm.boost.merged.seg \
	   $dir_work/${bn}.speech_sil.seg \
	   $dir_work

#cp -v $dir_work/${bn}.cv.seg $seg_out
python compress_segs.py -t $chunksize $dir_work/${bn}.cv.seg $seg_out
wc $seg_out
rm -r $dir_work

# -----------------------------------------------------------------------------

echo "Done (END)"

exit 0

