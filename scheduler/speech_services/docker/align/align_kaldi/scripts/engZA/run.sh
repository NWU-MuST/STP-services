#!/bin/bash

. ./cmd.sh ## You'll want to change cmd.sh to something that will work on your system.
           ## This relates to the queue.

# This is a shell script, but it's recommended that you run the commands one by
# one by copying and pasting into the shell.

if [ $# != 1 ]; then
	echo "usage: $0 <prep|mfcc|tri1|tri2a|tri2b|tri3a|tri3b>"
	exit 1
fi

if [ $1 == 'prep' ]; then

cp -r data_base/ data/

echo "preparing training"
utils/utt2spk_to_spk2utt.pl data/train/utt2spk > data/train/spk2utt
utils/fix_data_dir.sh data/train
utils/validate_data_dir.sh --no-feats data/train || exit 1

echo "preparing testing"
utils/utt2spk_to_spk2utt.pl data/test/utt2spk > data/test/spk2utt
utils/fix_data_dir.sh data/test
utils/validate_data_dir.sh --no-feats data/test || exit 1

echo "preparing lang"
utils/prepare_lang.sh data/local/dict "<unk>" data/local/lang_tmp data/lang || exit 1;

echo "preparing lang_test"
mkdir data/lang_test
mkdir data/tmp

cp -r data/lang/* data/lang_test/

gunzip -c data_base/lm/nchlt_eng.arpa.gz | \
   utils/find_arpa_oovs.pl data/lang_test/words.txt  > data/tmp/oovs.txt

gunzip -c data_base/lm/nchlt_eng.arpa.gz | \
    grep -v 'SIL SIL' | \
    arpa2fst - | fstprint | \
    utils/remove_oovs.pl data/tmp/oovs.txt | \
    utils/eps2disambig.pl | utils/s2eps.pl | fstcompile --isymbols=data/lang_test/words.txt \
      --osymbols=data/lang_test/words.txt  --keep_isymbols=false --keep_osymbols=false | \
     fstrmepsilon | fstarcsort --sort_type=ilabel > data/lang_test/G.fst

utils/validate_lang.pl --skip-determinization-check data/lang_test/ || exit 1;

fi

# Now make MFCC features.
# mfccdir should be some place with a largish disk where you
# want to store MFCC features.
mfccdir=mfcc
if [ $1 == "mfcc" ]; then
for x in train test; do
 echo "extracting mfcc for $x" 
 steps/make_mfcc.sh --cmd "$train_cmd" --nj 10 \
   data/$x exp/make_mfcc/$x $mfccdir || exit 1;
 steps/compute_cmvn_stats.sh data/$x exp/make_mfcc/$x $mfccdir || exit 1;
done
fi

if [ $1 == "mono" ]; then
# Note: the --boost-silence option should probably be omitted by default
# for normal setups.  It doesn't always help. [it's to discourage non-silence
# models from modeling silence.]
steps/train_mono.sh --boost-silence 1.25 --nj 10 --cmd "$train_cmd" \
  data/train data/lang exp/mono || exit 1;

 utils/mkgraph.sh --mono data/lang_test exp/mono exp/mono/graphs || exit 1;
 steps/decode.sh --nj 10 --cmd "$decode_cmd" \
      exp/mono/graphs data/test exp/mono/decode || exit 1;
fi

if [ $1 == "tri1" ]; then

steps/align_si.sh --boost-silence 1.25 --nj 10 --cmd "$train_cmd" \
   data/train data/lang exp/mono exp/mono_ali || exit 1;

steps/train_deltas.sh --boost-silence 1.25 --cmd "$train_cmd" \
    2000 10000 data/train data/lang exp/mono_ali exp/tri1 || exit 1;

utils/mkgraph.sh data/lang_test exp/tri1 exp/tri1/graphs || exit 1;

steps/decode.sh --nj 10 --cmd "$decode_cmd" \
  exp/tri1/graphs data/test exp/tri1/decode || exit 1;
fi

# test various modes of LM rescoring (4 is the default one).
# This is just confirming they're equivalent.
#for mode in 1 2 3 4; do
# steps/lmrescore.sh --mode $mode --cmd "$decode_cmd" data/lang_test_{tgpr,tg} \
#   data/test_dev93 exp/tri1/decode_tgpr_dev93 exp/tri1/decode_tgpr_dev93_tg$mode  || exit 1;
#done

# demonstrate how to get lattices that are "word-aligned" (arcs coincide with
# words, with boundaries in the right place).
#sil_label=`grep '!SIL' data/lang_test_tgpr/words.txt | awk '{print $2}'`
#steps/word_align_lattices.sh --cmd "$train_cmd" --silence-label $sil_label \
#  data/lang_test_tgpr exp/tri1/decode_tgpr_dev93 exp/tri1/decode_tgpr_dev93_aligned || exit 1;

if [ $1 == "tri2a" ]; then
steps/align_si.sh --nj 10 --cmd "$train_cmd" \
  data/train data/lang exp/tri1 exp/tri1_ali || exit 1;

# Train tri2a, which is deltas + delta-deltas, on si84 data.
steps/train_deltas.sh --cmd "$train_cmd" \
  2500 15000 data/train data/lang exp/tri1_ali exp/tri2a || exit 1;

utils/mkgraph.sh data/lang_test exp/tri2a exp/tri2a/graphs || exit 1;

steps/decode.sh --nj 10 --cmd "$decode_cmd" \
  exp/tri2a/graphs data/test exp/tri2a/decode || exit 1;
fi

if [ $1 == "tri2b" ]; then
steps/train_lda_mllt.sh --cmd "$train_cmd" \
   --splice-opts "--left-context=3 --right-context=3" \
   2500 15000 data/train data/lang exp/tri1_ali exp/tri2b || exit 1;

utils/mkgraph.sh data/lang_test exp/tri2b exp/tri2b/graphs || exit 1;
steps/decode.sh --nj 10 --cmd "$decode_cmd" \
  exp/tri2b/graphs data/test exp/tri2b/decode || exit 1;
fi

# baseline via LM rescoring of lattices.
#steps/lmrescore.sh --cmd "$decode_cmd" data/lang_test_tgpr/ data/lang_test_tg/ \
#  data/test_dev93 exp/tri2b/decode_tgpr_dev93 exp/tri2b/decode_tgpr_dev93_tg || exit 1;
# Trying Minimum Bayes Risk decoding (like Confusion Network decoding):
#mkdir exp/tri2b/decode_tgpr_dev93_tg_mbr 
#cp exp/tri2b/decode_tgpr_dev93_tg/lat.*.gz exp/tri2b/decode_tgpr_dev93_tg_mbr 
#local/score_mbr.sh --cmd "$decode_cmd" \
# data/test_dev93/ data/lang_test_tgpr/ exp/tri2b/decode_tgpr_dev93_tg_mbr
#steps/decode_fromlats.sh --cmd "$decode_cmd" \
#  data/test_dev93 data/lang_test_tgpr exp/tri2b/decode_tgpr_dev93 \
#  exp/tri2a/decode_tgpr_dev93_fromlats || exit 1

if [ $1 == "tri3a" ]; then
# Align tri2b system with si84 data.
# NTK: relabelled to tri3a
steps/align_si.sh  --nj 10 --cmd "$train_cmd" \
  --use-graphs true data/train data/lang exp/tri2b exp/tri2b_ali  || exit 1;

local/run_mmi_tri2b.sh
fi

if [ $1 == "tri3b" ]; then
# From 2b system, train 3b which is LDA + MLLT + SAT.
steps/train_sat.sh --cmd "$train_cmd" \
  4200 40000 data/train data/lang exp/tri2b_ali exp/tri3b || exit 1;
utils/mkgraph.sh data/lang_test exp/tri3b exp/tri3b/graphs || exit 1;
steps/decode_fmllr.sh --nj 10 --cmd "$decode_cmd" \
  exp/tri3b/graphs data/test exp/tri3b/decode || exit 1;
fi


if [ $1 == "tri4a" ]; then
# From 3b system, align all si284 data.
	steps/align_fmllr.sh --nj 20 --cmd "$train_cmd" \
	  data/train data/lang exp/tri3b exp/tri3b_ali || exit 1;
	local/run_mmi_tri4b.sh
fi

if [ $1 == "sgmm2" ]; then
	local/run_sgmm2.sh
fi

exit 0
# Train and test MMI, and boosted MMI, on tri4b (LDA+MLLT+SAT on
# all the data).  Use 30 jobs.
#steps/align_fmllr.sh --nj 30 --cmd "$train_cmd" \
#  data/train_si284 data/lang exp/tri4b exp/tri4b_ali_si284 || exit 1;

# These demonstrate how to build a sytem usable for online-decoding with the nnet2 setup.
# (see local/run_nnet2.sh for other, non-online nnet2 setups).
#local/online/run_nnet2.sh
#local/online/run_nnet2_baseline.sh
#local/online/run_nnet2_discriminative.sh



#local/run_nnet2.sh

## Segregated some SGMM builds into a separate file.
#local/run_sgmm.sh

# You probably want to run the sgmm2 recipe as it's generally a bit better:


# We demonstrate MAP adaptation of GMMs to gender-dependent systems here.  This also serves
# as a generic way to demonstrate MAP adaptation to different domains.
# local/run_gender_dep.sh

# You probably want to run the hybrid recipe as it is complementary:
local/nnet/run_dnn.sh

# The following demonstrate how to re-segment long audios.
# local/run_segmentation.sh

# The next two commands show how to train a bottleneck network based on the nnet2 setup,
# and build an SGMM system on top of it.
#local/run_bnf.sh
#local/run_bnf_sgmm.sh


# You probably want to try KL-HMM 
#local/run_kl_hmm.sh

# Getting results [see RESULTS file]
# for x in exp/*/decode*; do [ -d $x ] && grep WER $x/wer_* | utils/best_wer.sh; done


# KWS setup. We leave it commented out by default

# $duration is the length of the search collection, in seconds
#duration=`feat-to-len scp:data/test_eval92/feats.scp  ark,t:- | awk '{x+=$2} END{print x/100;}'`
#local/generate_example_kws.sh data/test_eval92/ data/kws/
#local/kws_data_prep.sh data/lang_test_bd_tgpr/ data/test_eval92/ data/kws/
#
#steps/make_index.sh --cmd "$decode_cmd" --acwt 0.1 \
#  data/kws/ data/lang_test_bd_tgpr/ \
#  exp/tri4b/decode_bd_tgpr_eval92/ \
#  exp/tri4b/decode_bd_tgpr_eval92/kws
#
#steps/search_index.sh --cmd "$decode_cmd" \
#  data/kws \
#  exp/tri4b/decode_bd_tgpr_eval92/kws
#
# If you want to provide the start time for each utterance, you can use the --segments
# option. In WSJ each file is an utterance, so we don't have to set the start time.
#cat exp/tri4b/decode_bd_tgpr_eval92/kws/result.* | \
#  utils/write_kwslist.pl --flen=0.01 --duration=$duration \
#  --normalize=true --map-utter=data/kws/utter_map \
#  - exp/tri4b/decode_bd_tgpr_eval92/kws/kwslist.xml

# # forward-backward decoding example [way to speed up decoding by decoding forward
# # and backward in time] 
# local/run_fwdbwd.sh
