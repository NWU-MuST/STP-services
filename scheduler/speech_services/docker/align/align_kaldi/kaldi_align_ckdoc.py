#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
"""
from __future__ import unicode_literals, division, print_function #Py2

__author__ = "Daniel van Niekerk"
__email__ = "dvn.demitasse@gmail.com"

import sys, os
import codecs
import re
import wave
import contextlib
#import multiprocessing

sys.path.append(os.path.join(os.getenv("ALIGNKALDI_ROOT")))
from normmaphtml2utf8 import preproc_normmap
from kaldi_align_text import do_align
from setuplog import LOG

#DEF_NCPUS = multiprocessing.cpu_count()

DEF_LANG = "engZA"

TIMESTAMP_RE = '<p><time[^<>]*?type="mark"[^<>]*?>[^<>]*?</time></p>'
STRIPOLD_RE = "<[/]?time[^<>]*?>|<[/]?conf[^<>]*?>"
FAILTHRESH = 20.0 #if list of aligned tokens is % shorter than simple text tokens we assume catastrophic failure...
UNK = "<unk>"
SIL = "SIL"

def align_wrap(args):
    wavfn, starttime, endtime, text, lang = args
    if text.strip() == "" or (endtime - starttime) == 0.0:
        return None
    return do_align(args)


def mapback(cmapa, revcmapb, i):
    ii = (len(cmapa) - revcmapb.index(i)) - 1
    return cmapa[ii]

def string_insert(orig, substr, i):
    return orig[:i] + substr + orig[i:]

def strip_old(htmltext):
    """This removes previous alignment and confidence tags before
       running alignment..
    """
    return re.sub(STRIPOLD_RE, "", htmltext)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('inwavfn', metavar='INWAVFN', type=str, help="input wave file")
    parser.add_argument('indocfn', metavar='INDOCFN', type=str, help="input html file (CKEditor HTML in UTF-8)")
    parser.add_argument('outdocfn', metavar='OUTDOCFN', type=str, help="output html file (CKEditor HTML in UTF-8)")
    #parser.add_argument('--ncpus', metavar='NCPUS', type=int, dest="ncpus", default=DEF_NCPUS, help="number of CPUs used")
    parser.add_argument('--lang', metavar='LANG', type=str, dest="lang", default=DEF_LANG, help="language (selects appropriate scripts and models)")
    
    args = parser.parse_args()
    #POOL = multiprocessing.Pool(processes=args.ncpus)
    #def map(f, i):
    #    return POOL.map(f, i, chunksize=1)

    #LOAD:
    with contextlib.closing(wave.open(args.inwavfn, "r")) as infh:
        wavduration = infh.getnframes() / float(infh.getframerate())
    with codecs.open(args.indocfn, encoding="utf-8") as infh:
        doc = " ".join(infh.read().splitlines())

    #SPLIT JOBS AND CLEAN-UP:
    timestamps = re.findall(TIMESTAMP_RE, doc)
    starttime = 0.0
    startendtimes = []
    for timestamp in timestamps:
        endtime = float(re.search('datetime="(.*?)"', timestamp).group(1))
        startendtimes.append((starttime, endtime))
        starttime = endtime
    startendtimes.append((starttime, wavduration))
    htmltexts = map(strip_old, re.split(TIMESTAMP_RE, doc))

    #PROCESSING:
    prep_norm_maps = map(preproc_normmap, htmltexts)
    # for p, n, m in prep_norm_maps:
    #     print("\n", p)
    #     print(n)
    assert len(prep_norm_maps) == len(startendtimes)
    alignargs = [(se[0], se[1], pnm[1]) for se, pnm in zip(startendtimes, prep_norm_maps)]
    alignments = map(align_wrap, [(args.inwavfn, starttime, endtime, text, args.lang) for starttime, endtime, text in alignargs])

    #INSERT TIMESTAMPS:
    newhtmls = []
    for alignment, startendtime, prep_norm_map in zip(alignments, startendtimes, prep_norm_maps):
        if alignment is None:
            LOG.info("Alignment not done for ...")
            newhtmls.append("")
        else:
            alignlen = len([e for e in alignment if e[1] not in [UNK, SIL]])
            textlen = len(prep_norm_map[1].split())
            LOG.info("TEXTLEN, ALIGNLEN: %s, %s" % (textlen, alignlen))
            if (textlen - alignlen) > 0 and (float(abs(textlen - alignlen)) / textlen * 100) > FAILTHRESH:
                LOG.info("Alignment looks BAD for ...")
                newhtmls.append(re.sub('<p>(.*?)</p>', '<p><conf style="background-color: #FFFF00">\\1</conf></p>', prep_norm_map[0]))
            else:
                LOG.info("Alignment looks OK for ...")
                newhtml = prep_norm_map[0]
                cmapa, revcmapb = [e[0] for e in prep_norm_map[2]], list(reversed([e[1] for e in prep_norm_map[2]]))
                starttime = startendtime[0]
                timeedits = []
                confedits = []
                for ppa, pa, ca, na, nna in zip([None, None] + alignment,
                                                [None] + alignment,
                                                alignment,
                                                alignment[1:] + [None],
                                                alignment[2:] + [None, None]):
                    time, token = ca
                    #print(time, token)
                    try:
                        indices = map(int, re.search("<(\d+),(\d+)>$", token).group(1, 2))
                    except AttributeError:
                        continue
                    timeedits.append((mapback(cmapa, revcmapb, indices[0]), '<time datetime="{:.3f}">'.format(starttime + time)))
                    timeedits.append((mapback(cmapa, revcmapb, indices[1]-1), '</time>'))
                    if pa and pa[1] == "<unk>":
                        confedits.append((mapback(cmapa, revcmapb, indices[0]), '<conf style="background-color: #FFA500">'))
                        confedits.append((mapback(cmapa, revcmapb, indices[1]-1), '</conf>'))
                    elif na and na[1] == "<unk>":
                        confedits.append((mapback(cmapa, revcmapb, indices[0]), '<conf style="background-color: #FFA500">'))
                        confedits.append((mapback(cmapa, revcmapb, indices[1]-1), '</conf>'))
                    elif ppa and ppa[1] == "<unk>" and pa and pa[1] == "SIL":
                        confedits.append((mapback(cmapa, revcmapb, indices[0]), '<conf style="background-color: #FFA500">'))
                        confedits.append((mapback(cmapa, revcmapb, indices[1]-1), '</conf>'))
                    elif nna and nna[1] == "<unk>" and na and na[1] == "SIL":
                        confedits.append((mapback(cmapa, revcmapb, indices[0]), '<conf style="background-color: #FFA500">'))
                        confedits.append((mapback(cmapa, revcmapb, indices[1]-1), '</conf>'))
                timeedits = dict(set(timeedits))
                confedits = dict(set(confedits))
                idxs = sorted(set(timeedits.keys() + confedits.keys()), reverse=True)
                for idx in idxs:
                    if idx in confedits:
                        newhtml = string_insert(newhtml, confedits[idx], idx)
                    if idx in timeedits:
                        newhtml = string_insert(newhtml, timeedits[idx], idx)
                newhtmls.append(newhtml)
    newdoc = ""
    for i, newhtml in enumerate(newhtmls):
        try:
            newdoc += newhtml + timestamps[i]
        except IndexError:
            newdoc += newhtml

    #PRETTIFY DOC AND SAVE:
    newdoc = newdoc.replace("</p>", "</p>\n\n")
    newdoc = newdoc.replace("<br />", "<br />\n")
    with codecs.open(args.outdocfn, "w", encoding="utf-8") as outfh:
        outfh.write(newdoc)
