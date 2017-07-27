#!/bin/bash

LC_ALL=C

if [ $# -ne 2 ]; then
	echo "usage: $0 wordlist symbol"
	exit 1
fi

cat $1 | awk '{print $1}' | sort | uniq  | awk '
  BEGIN {
    print "<eps> 0";
    print "<unk> 1";
    print "SIL 2";
  } 
  {
    if ($1 == "<s>") {
      print "<s> is in the vocabulary!" | "cat 1>&2"
      exit 1;
    }
    if ($1 == "</s>") {
      print "</s> is in the vocabulary!" | "cat 1>&2"
      exit 1;
    }
    printf("%s %d\n", $1, NR+2);
  }
  END {
    printf("#0 %d\n", NR+2+1);
  }' > $2 || exit 1;


#    printf("<s> %d\n", NR+1+2);
#    printf("</s> %d\n", NR+1+3);
