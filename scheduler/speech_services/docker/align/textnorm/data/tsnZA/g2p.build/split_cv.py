import codecs
import sys
import os
import random

if len(sys.argv) != 3:
    print "{} in_list out_dir".format(sys.argv[0])
    sys.exit(1)

if not os.path.exists(sys.argv[2]):
    os.mkdir(sys.argv[2])

with codecs.open(sys.argv[1], "r", "utf-8") as f:
    tsn = f.readlines()
    tsn = [x.strip(u"\n") for x in tsn]
    random.shuffle(tsn)

cv = {}
for n in range(10):
    cv[n] = []

n = 0
for pron in tsn:
    if n == 10:
        n = 0

    cv[n].append(pron)
    n += 1

for n in range(10):
    with codecs.open(os.path.join(sys.argv[2], "trn.{}.txt".format(n)), "w", "utf-8") as trn, codecs.open(os.path.join(sys.argv[2], "tst.{}.txt".format(n)), "w", "utf-8") as tst:
        for m in range(10):
            if n != m:
                trn.write(u"\n".join(cv[m]))
                trn.write(u"\n")
            else:
                tst.write(u"\n".join(cv[m]))
                tst.write(u"\n")

