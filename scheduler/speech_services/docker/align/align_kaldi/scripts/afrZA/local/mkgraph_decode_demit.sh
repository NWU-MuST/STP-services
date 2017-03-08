#!/bin/bash
# Copyright 2010-2012 Microsoft Corporation
#           2012-2013 Johns Hopkins University (Author: Daniel Povey)
# Apache 2.0

# This script creates a fully expanded decoding graph (HCLG) that represents
# all the language-model, pronunciation dictionary (lexicon), context-dependency,
# and HMM structure in our model.  The output is a Finite State Transducer
# that has word-ids on the output, and pdf-ids on the input (these are indexes
# that resolve to Gaussian Mixture Models).  
# See
#  http://kaldi.sourceforge.net/graph_recipe_test.html
# (this is compiled from this repository using Doxygen,
# the source for this part is in src/doc/graph_recipe_test.dox)


N=3
P=1
tscale=1.0
loopscale=0.1

reverse=false

for x in `seq 5`; do 
  [ "$1" == "--mono" ] && N=1 && P=0 && shift;
  [ "$1" == "--quinphone" ] && N=5 && P=2 && shift;
  [ "$1" == "--reverse" ] && reverse=true && shift;
  [ "$1" == "--transition-scale" ] && tscale=$2 && shift 2;
  [ "$1" == "--self-loop-scale" ] && loopscale=$2 && shift 2;
done

if [ $# != 4 ]; then
   echo "Usage: utils/mkgraph.sh [options] <lang-dir> <model-dir> <in-g-fst-dir> <graphdir>"
   echo "e.g.: utils/mkgraph.sh data_decode/lang_test exp/tri1/ G.fst exp/tri1/graph"
   echo " Options:"
   echo " --mono          #  For monophone models."
   echo " --quinphone     #  For models with 5-phone context (3 is default)"
   exit 1;
fi

if [ -f path.sh ]; then . ./path.sh; fi

lang=$1
tree=$2/tree
model=$2/final.mdl
g_fst=$3
dir=$4

outdir=`dirname $g_fst`
mkdir -p $dir

# If $lang/tmp/LG.fst does not exist or is older than its sources, make it...
# (note: the [[ ]] brackets make the || type operators work (inside [ ], we
# would have to use -o instead),  -f means file exists, and -ot means older than).

required="$lang/L.fst $lang/phones.txt $lang/words.txt $lang/phones/silence.csl $lang/phones/disambig.int $model $tree"
for f in $required; do
  [ ! -f $f ] && echo "mkgraph.sh: expected $f to exist" && exit 1;
done

tmpdir=`dirname $lang`
tmpdir="$tmpdir/tmp"
mkdir -p $tmpdir
rm -f $tmpdir/*

#echo "cat $g_fst |  utils/eps2disambig.pl | utils/s2eps.pl | fstcompile --isymbols=$lang/words.txt \
#      --osymbols=$lang/words.txt  --keep_isymbols=false --keep_osymbols=false | \
#     fstrmepsilon | fstarcsort --sort_type=ilabel > $tmpdir/G.fst"

#DEMITASSE: DELETE
# cut -f 1-4 $g_fst |  utils/eps2disambig.pl | utils/s2eps.pl | fstcompile --isymbols=$lang/words.txt \
#     --osymbols=$lang/words.txt  --keep_isymbols=false --keep_osymbols=false | \
#     fstrmepsilon | fstarcsort --sort_type=ilabel > $tmpdir/G_orig.fst

cat $g_fst | \
    fstcompile --isymbols=$lang/words.txt --osymbols=$lang/words.txt  --keep_isymbols=false --keep_osymbols=false | \
    fstarcsort --sort_type=ilabel > $tmpdir/G.fst || exit 1;

#fstrmepsilon $g_fst | fstarcsort --sort_type=ilabel > $tmpdir/G.fst
#fstarcsort --sort_type=ilabel $g_fst > $tmpdir/G.fst

# Note: [[ ]] is like [ ] but enables certain extra constructs, e.g. || in 
# place of -o
fsttablecompose $lang/L_disambig.fst $tmpdir/G.fst | \
    fstarcsort --sort_type=ilabel > $tmpdir/LG.fst || exit 1;
# fsttablecompose $lang/L_disambig.fst $tmpdir/G.fst | \
#     fstdeterminizestar --use-log=true | \
#     fstminimizeencoded | \
#     fstarcsort --sort_type=ilabel > $tmpdir/LG.fst || exit 1;
fstisstochastic $tmpdir/LG.fst || echo "[info]: LG not stochastic."


#fsttablecompose $lang/L.fst $tmpdir/G.fst | fstarcsort --sort_type=ilabel > $tmpdir/LG.fst || exit 1;
#fstisstochastic $tmpdir/LG.fst || echo "[info]: LG not stochastic."

clg=$tmpdir/CLG_${N}_${P}.fst

fstcomposecontext --context-size=$N --central-position=$P \
   --read-disambig-syms=$lang/phones/disambig.int \
   --write-disambig-syms=$tmpdir/disambig_ilabels_${N}_${P}.int \
    $tmpdir/ilabels_${N}_${P} < $tmpdir/LG.fst |\
    fstarcsort --sort_type=ilabel > $clg || exit 1;
fstisstochastic $clg  || echo "[info]: CLG not stochastic."


if $reverse; then
    make-h-transducer --reverse=true --push_weights=true \
	--disambig-syms-out=$tmpdir/disambig_tid.int \
	--transition-scale=$tscale $tmpdir/ilabels_${N}_${P} $tree $model \
	> $tmpdir/Ha.fst  || exit 1;
else
    make-h-transducer \
	--disambig-syms-out=$tmpdir/disambig_tid.int \
	--transition-scale=$tscale $tmpdir/ilabels_${N}_${P} $tree $model \
	> $tmpdir/Ha.fst  || exit 1;
fi

# fsttablecompose $tmpdir/Ha.fst $clg | fstdeterminizestar --use-log=true \
#     | fstrmepslocal | fstminimizeencoded > $tmpdir/HCLGa.fst || exit 1;
# #fsttablecompose $tmpdir/Ha.fst $clg > $tmpdir/HCLGa.fst || exit 1;
# fstisstochastic $tmpdir/HCLGa.fst || echo "HCLG is not stochastic"

# fsttablecompose $tmpdir/Ha.fst $clg | \
#     fstdeterminizestar --use-log=true | \
#     fstrmsymbols $tmpdir/disambig_tid.int | \
#     fstrmepslocal | \
#     fstminimizeencoded > $tmpdir/HCLGa.fst || exit 1;
fsttablecompose $tmpdir/Ha.fst $clg | \
    fstrmsymbols $tmpdir/disambig_tid.int | \
    fstrmepslocal > $tmpdir/HCLGa.fst || exit 1;
fstisstochastic $tmpdir/HCLGa.fst || echo "HCLGa is not stochastic"


add-self-loops --self-loop-scale=0 --reorder=true \
   $model < $tmpdir/HCLGa.fst > $outdir/HCLG.fst || exit 1;

#if [[ ! -s $dir/HCLG.fst || $dir/HCLG.fst -ot $dir/HCLGa.fst ]]; then
#  add-self-loops --self-loop-scale=$loopscale --reorder=true \
#    $model < $dir/HCLGa.fst > $dir/HCLG.fst || exit 1;

#  if [ $tscale == 1.0 -a $loopscale == 1.0 ]; then
    # No point doing this test if transition-scale not 1, as it is bound to fail. 
#    fstisstochastic $dir/HCLG.fst || echo "[info]: final HCLG is not stochastic."
#  fi
#fi

# keep a copy of the lexicon and a list of silence phones with HCLG...
# this means we can decode without reference to the $lang directory.

#cp $lang/words.txt $dir/ || exit 1;
#mkdir -p $dir/phones
#cp $lang/phones/word_boundary.* $dir/phones/ 2>/dev/null # might be needed for ctm scoring,
#cp $lang/phones/align_lexicon.* $dir/phones/ 2>/dev/null # might be needed for ctm scoring,
  # but ignore the error if it's not there.

#cp $lang/phones/disambig.{txt,int} $dir/phones/ 2> /dev/null
#cp $lang/phones/silence.csl $dir/phones/ || exit 1;
#cp $lang/phones.txt $dir/ 2> /dev/null # ignore the error if it's not there.

# to make const fst:
# fstconvert --fst_type=const $dir/HCLG.fst $dir/HCLG_c.fst
#am-info --print-args=false $model | grep pdfs | awk '{print $NF}' > $dir/num_pdfs

