#!/bin/bash
set -e
#TODO: Check CLI arguments
export LC_ALL=C

LANG=$1
OUTDIR=$2
shift 2

###TEXTNORM_ROOT from the environment
G2PMODEL=$MODEL_ROOT/data/$LANG/g2pmodel.pickle
CHARDICT=$MODEL_ROOT/data/$LANG/chardict.txt
UNKDEF=$MODEL_ROOT/data/$LANG/unk.txt
SILDEF=$MODEL_ROOT/data/$LANG/sil.txt

SENT2FST="$TEXTNORM_ROOT/sent2fst.py $LANG"
WORDS2SYMTAB=$TEXTNORM_ROOT/words2symtab.sh
FSTRESYM=$TEXTNORM_ROOT/fstresym.py
FST4ALIGN=$TEXTNORM_ROOT/fst4align.py
PRONUN=$TEXTNORM_ROOT/pronun.py 

tmpdir=`mktemp -d`

#clean words for g2p
wordset () {
    fstprint $1 | \
	sed -r 's/<.*>(.*)$/\1/g' | \
	cut -f 4 | \
	sed 's/^[0-9]*$//g' | \
	sort -u | \
	sed '/^$/d'
}

#words with "token tags"
wordset_tok () {
    fstprint $1 | \
	cut -f 4 | \
	sed 's/^[0-9]*$//g' | \
	sort -u | \
	sed '/^$/d'
}
    
#TOKENISE/NORMALISE AND CREATE BASIC FSTS
for fn in $*; do
    python $SENT2FST < $fn > $tmpdir/`basename $fn .txt`.rawfst
done

#TRIM FSTS (DEMITASSE: Check somewhere to ensure no duplicate paths?)
for fn in $tmpdir/*.rawfst; do
    fstconnect $fn | fstdeterminize | fstminimize > $tmpdir/`basename $fn .rawfst`.trimfst
done

#MAKE KALDI SYMBOL TABLE AND MAP FST SYMBOLS (DEMITASSE TODO: Check whether this corresponds...)
#Make disambig wordlist and Kaldi symtab
for fn in $tmpdir/*.trimfst; do
    wordset_tok $fn
done | sort -u > $tmpdir/wordlist.tok
bash $WORDS2SYMTAB $tmpdir/wordlist.tok $tmpdir/symtab.txt
#Map symbols
for fn in $tmpdir/*.trimfst; do
    fstprint $fn | \
	python $FSTRESYM $tmpdir/symtab.txt | \
	fstcompile > $tmpdir/`basename $fn .trimfst`.mappedfst
done

#ADD UNKS AND SKIPS
for fn in $tmpdir/*.mappedfst; do
    python $FST4ALIGN $tmpdir/symtab.txt < $fn | \
	fstprint --isymbols=$tmpdir/symtab.txt --osymbols=$tmpdir/symtab.txt > $tmpdir/`basename $fn .mappedfst`.fst
done

#CREATE PRONUNCIATION DICTIONARY USING G2P + CHARDICT
python $PRONUN $CHARDICT $G2PMODEL < $tmpdir/wordlist.tok > $tmpdir/lexicon.txt
cat $UNKDEF >> $tmpdir/lexicon.txt
cat $SILDEF >> $tmpdir/lexicon.txt

#CLEANUP
cp $tmpdir/*.fst $tmpdir/symtab.txt $tmpdir/lexicon.txt $OUTDIR
rm -fr $tmpdir
