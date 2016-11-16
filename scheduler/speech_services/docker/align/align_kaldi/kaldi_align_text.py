#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Create temporary environment and perform Kaldi decode from simple
wave file (with times) and Text (UTF-8)...
"""
from __future__ import unicode_literals, division, print_function #Py2

__author__ = "Daniel van Niekerk"
__email__ = "dvn.demitasse@gmail.com"

import sys, os
import codecs
import shutil
from tempfile import mkdtemp
import tarfile
import subprocess
import gzip
import re

#setup logging...
from setuplog import LOG

#stdout = subprocess.check_output(cmd, shell=True)

MODELS_ROOT = os.path.join(os.getenv("MODEL_ROOT"), "models")
SCRIPTS_ROOT = os.path.join(os.getenv("ALIGNKALDI_ROOT"), "scripts")

DEF_LANG = "engZA"

DEF_ACWT = 0.08333
UNK = "<unk>"
SIL = "SIL"
DO_CTM = None

class ShellException(Exception):
    pass

def do_align(args):
    def shell(cmd):
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = proc.communicate()
        if proc.returncode:
            LOG.error("STDOUT:\n" + unicode(stdout, encoding="utf-8"))
            LOG.error("##############################")
            LOG.error("STDERR:\n" + unicode(stderr, encoding="utf-8"))
            LOG.error("##############################")
            raise ShellException("SHELL error: {}".format(cmd))
        LOG.info("SHELL success: {}".format(cmd))    
        return stdout, stderr
    ####
    inwavfn, starttime, endtime, text, lang = args
    
    acwt = DEF_ACWT
    try:
        #SETUP WAV, TEXT AND MODELS...
        tempdir = mkdtemp(prefix="align_kaldi_")
        t = tarfile.open(os.path.join(SCRIPTS_ROOT, lang + ".tar"), "r:*")
        t.extractall(tempdir)
        shell("sox {inwavfn} {outwavfn} trim {starttime} {duration}".format(inwavfn=inwavfn,
                                                                            outwavfn=os.path.join(tempdir, "data_decode/wav/UTTERANCE.wav"),
                                                                            starttime=starttime,
                                                                            duration=endtime - starttime))
        with open(os.path.join(tempdir, "data_decode/decode/wav.scp_"), "w") as outfh:
            outfh.write(" ".join(["UTTERANCE", os.path.join(tempdir, "data_decode/wav/UTTERANCE.wav")]) + "\n")
        with codecs.open(os.path.join(tempdir, "data_decode/decode/text_"), "w", encoding="utf-8") as outfh:
            outfh.write(" ".join(["UTTERANCE", text]) + "\n")
        with codecs.open(os.path.join(tempdir, "data_decode/decode/textnorm_"), "w", encoding="utf-8") as outfh:
            outfh.write(text + "\n")
        cwd = os.getcwd()
        os.chdir(tempdir)
        os.makedirs("exp")
        os.chdir("exp")
        os.makedirs("0")
        os.makedirs("1")
        os.chdir("0")
        for fn in os.listdir(os.path.join(MODELS_ROOT, lang + "0")):
            os.symlink(os.path.join(MODELS_ROOT, lang + "0", fn), fn)
        os.chdir("../1")
        for fn in os.listdir(os.path.join(MODELS_ROOT, lang + "1")):
            os.symlink(os.path.join(MODELS_ROOT, lang + "1", fn), fn)
        os.chdir("../..")
        #TEXTNORM-ALIGNMENT PROCESS
        #do stuff
        shell("./decode.sh textnorm")
        shell("./decode.sh prep")
        shell("./decode.sh mkgraph")
        shell("./decode.sh mfcc")
        for i in range(2):
            LOG.info("Doing decode with ACWT={}".format(acwt))
            stderr, stdout = shell("./decode.sh decode {}".format(acwt))
            LOG.debug("DECODE STDOUT:\n" + unicode(stdout, encoding="utf-8"))
            LOG.debug("##############################")
            LOG.debug("DECODE STDERR:\n" + unicode(stderr, encoding="utf-8"))
            LOG.debug("##############################")
            stderr, stdout = shell("./decode.sh ctm {}".format(acwt))
            LOG.debug("CTM STDOUT:\n" + unicode(stdout, encoding="utf-8"))
            LOG.debug("##############################")
            LOG.debug("CTM STDERR:\n" + unicode(stderr, encoding="utf-8"))
            LOG.debug("##############################")
            nsucc, nerrs = map(int, re.search("LOG \(lattice\-align\-words\:main\(\)\:lattice\-align\-words\.cc\:125\) Successfully aligned (\d+) lattices; (\d+) had errors.", stdout).groups())
            if not nerrs:
                break
            acwt *= 0.1
            LOG.info("CTM: Partial lattice...")
        #get stuff
        if DO_CTM is None:
            starttimes = []
            with gzip.open("exp_align/ctm.ctm.gz") as infh:
                alignments = unicode(infh.read(), encoding="utf-8")
            for line in alignments.splitlines():
                fields = line.split()
                starttimes.append((float(fields[2]), fields[4]))
        else:
            with gzip.open("exp_align/ctm.ctm.gz") as infh, codecs.open(DO_CTM, "w", "utf-8") as outfh:
                outfh.write(unicode(infh.read(), encoding="utf-8"))
            starttimes = []

    except ShellException as e:
        LOG.error(str(e) + " (see stdout and stderr)")
        return [] #empty starttimes
    except (OSError, IOError) as e:
        LOG.error(e)
        return [] #empty starttimes
    finally:
        os.chdir(cwd)
        shutil.rmtree(tempdir)
    return starttimes

if __name__ == "__main__":
    import wave
    import contextlib
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('inwavfn', metavar='INWAVFN', type=str, help="input wave file")
    parser.add_argument('intxtfn', metavar='INTXTFN', type=str, help="input text (UTF-8)")
    parser.add_argument('--starttime', metavar='STARTTIME', type=float, help="utterance start time (in seconds)")
    parser.add_argument('--endtime', metavar='ENDTIME', type=float, help="utterance end time (in seconds)")
    parser.add_argument('--lang', metavar='LANG', type=str, dest="lang", default=DEF_LANG, help="language (selects appropriate scripts and models)")
    parser.add_argument('--ctm', metavar='CTM', type=str, dest="ctm", help="Output the raw CTM to file")

    args = parser.parse_args()

    if args.ctm is not None:
        DO_CTM = args.ctm

    if args.starttime is None:
        starttime = 0.0
    else:
        starttime = args.starttime
    if args.endtime is None:
        with contextlib.closing(wave.open(args.inwavfn, "r")) as infh:
            endtime = infh.getnframes() / float(infh.getframerate())

    with codecs.open(args.intxtfn, encoding="utf-8") as infh:
        text = " ".join(infh.read().split())

    LOG.debug("TEXT: " + text)
    starttimes = do_align((args.inwavfn, starttime, endtime, text, args.lang))
    if not args.ctm:
        for entry in starttimes:
            print(entry[0], entry[1])
        contententries = [e[1] for e in starttimes if e[1] not in [UNK, SIL]]
        LOG.debug(" ".join(map(str, [len(text.split()), len(contententries)])))
    else:
        print(starttimes)

