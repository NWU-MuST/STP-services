#!/bin/bash
set -e

source ./cmd.sh
source ./path.sh

#DEMIT: acwt default was 0.08333
#ACWT=0.008333

if [ $# -lt 1 ]; then
    echo "usage: $0 <textnorm|prep|mfcc|mkgraph|decode|ctm|phctm|all>"
    exit 1
fi

if [ $1 == "clean" ]; then
    rm -r data_align exp_align mfcc_align
fi

if [ $1 == 'textnorm' ] || [ $1 == 'all' ]; then
    mkdir data_decode/fst
    bash $TEXTNORM_ROOT/do_for_alignment.sh engZA data_decode/fst data_decode/decode/textnorm
    ln -s ../../fst/lexicon.txt data_decode/local/dict/lexicon.fromtextnorm
fi


if [ $1 == 'prep' ] || [ $1 == 'all' ]; then
    echo "preparing alignment"
    utils/utt2spk_to_spk2utt.pl data_decode/decode/utt2spk > data_decode/decode/spk2utt
    utils/fix_data_dir.sh data_decode/decode
    utils/validate_data_dir.sh --no-feats data_decode/decode
    
    echo "preparing lang"
    echo "local/prepare_lang.sh data_decode/local/dict \"<unk>\" data_decode/local/lang_tmp data_decode/lang"
    local/prepare_lang.sh data_decode/local/dict "<unk>" data_decode/local/lang_tmp data_decode/lang
    echo ""
    echo "DEMITASSE: CHECKING SYMBOL TABLES (TEXTNORM vs PREP_LANG):"
    diff data_decode/fst/symtab.txt data_decode/lang/words.txt
    if [ $? -eq 0 ]; then
	echo "OK!"
    else
	echo "ERROR.... SYMBOL TABLES DIFFER!"
	exit 1
    fi
fi

mfccdir=mfcc_align
if [ $1 == "mfcc" ] || [ $1 == 'all' ]; then
    echo "extracting mfcc for align" 
    steps/make_mfcc.sh --cmd "$train_cmd" --nj 1 \
	data_decode/decode exp_align/make_mfcc/decode $mfccdir
    steps/compute_cmvn_stats.sh data_decode/decode exp_align/make_mfcc/decode $mfccdir
fi

if [ $1 == 'mkgraph' ] || [ $1 == 'all' ]; then
    local/mkgraph_decode_demit.sh data_decode/lang exp/0/ data_decode/fst/textnorm.fst exp_decode/graph
fi

if [ $1 == 'decode' ] || [ $1 == 'all' ]; then
    ACWT=$2
    local/decode_fmllr_extra_must.sh --nj 1 --acwt $ACWT --cmd "$decode_cmd" data_decode/fst/HCLG.fst exp/0/graphs data_decode/decode exp/0/demit_decode
    #local/decode_sgmm2_must.sh --nj 1 --acwt $ACWT --cmd "$decode_cmd" --transform-dir exp/0/demit_decode data_decode/fst/HCLG.fst exp/1/graphs data_decode/decode exp/1/demit_decode
fi

if [ $1 == "ctm" ] || [ $1 == 'all' ]; then
    ACWT=$2
    echo "extracting ctm"
    model="exp/0/final.mdl"
    lang="data_decode/lang"
    oov=`cat $lang/oov.int`

    lattice-push ark:'gunzip -c exp/0/demit_decode.si/lat.1.gz|' ark:- | \
	lattice-align-words --silence-label=2 $lang/phones/word_boundary.int $model ark:- ark:- | \
	lattice-to-ctm-conf --acoustic-scale=$ACWT ark:- - | \
	utils/int2sym.pl -f 5 $lang/words.txt | \
	gzip -c > exp_align/ctm.${1}.gz

fi

if [ $1 == "phctm" ]; then
    ACWT=$2
    echo "extracting ctm"
    model="exp/0/final.mdl"
    lang="data_decode/lang"
    oov=`cat $lang/oov.int`

    lattice-push ark:'gunzip -c exp/0/demit_decode/lat.1.gz|' ark:- | \
	lattice-align-phones --replace-output-symbols $model ark:- ark:- | \
	lattice-to-ctm-conf --acoustic-scale=$ACWT ark:- - | \
	utils/int2sym.pl -f 5 $lang/phones.txt | \
	gzip -c > exp_align/ctm.${1}.gz

fi
