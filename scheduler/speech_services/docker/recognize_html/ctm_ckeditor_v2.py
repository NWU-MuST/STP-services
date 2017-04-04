#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, division, print_function #Py2

import os
import sys
import codecs
import datetime
import re

def extract_segments(workname, segs):
        #C[1]      0.00000     22.56000
        seg_info = {}
        seg_content = {}
        seg_order = []

        for line in segs:
                (tag, start, end) = line.split()
                #if tag != "sil":
                fstart = float('%.2f' % float(start))
                fend = float('%.2f' % float(end))

                start = '{}0000'.format(start)
                end = '{}0000'.format(end)
                match = re.search('(\d+)\.(\d\d)', str(start))
                sstart = u'{}{}'.format(match.group(1), match.group(2)).zfill(6)
                match = re.search('(\d+)\.(\d\d)', str(end))
                send = u'{}{}'.format(match.group(1), match.group(2)).zfill(6)

                utt = '{}-{}-{}'.format(workname, sstart, send)
                print(utt)
                seg_order.append(utt)
                seg_info[utt] = (fstart, fend)
                seg_content[utt] = []

        return seg_order, seg_info, seg_content

def extract_segment_content(seg_info, seg_content, ali):
        #A-001187-001760 1 1.91 0.03 sil 1.00
        for line in ali:
                (utt, channel, start, end, word, conf) = line.split()
                true_start = seg_info[utt][0]
                new_start = '%.2f' % (true_start + float(start))
                #new_end = '%.2f' % (float(start) + float(end))
                seg_content[utt].append((float(new_start), word, float(conf)))

        return seg_content


if __name__ == "__main__":

        if len(sys.argv) != 6:
                print('Usage: %s workname segments inter ctm out_ckeditor_html' % sys.argv[0])
                sys.exit(1)

        workname = sys.argv[1]
        segments = sys.argv[2]
        inter = sys.argv[3]
        ctm = sys.argv[4]
        out_html = sys.argv[5]

        with codecs.open(segments, 'r', 'utf-8') as f:
                segs = f.readlines()
        segs = [x.strip('\n') for x in segs]

        with codecs.open(ctm, 'r', 'utf-8') as f:
                ali = f.readlines()
        ali = [x.strip('\n') for x in ali]

        with codecs.open(inter, 'r', 'utf-8') as f:
                html = f.readlines()
        html = [x.strip('\n') for x in html]

        html_time = []
        html_content = []
        for line in html:
                toks = line.split(u'#$%')
                html_time.append(toks.pop(0))
                if len(toks) == 1 and len(toks[0]) == 0:
                        html_content.append(u'')
                else:
                        html_content.append(u'\n'.join(toks))

        seg_order, seg_info, seg_content = extract_segments(workname, segs)
        #print(seg_order, seg_info)
        seg_content = extract_segment_content(seg_info, seg_content, ali)
        #print(seg_content)
        #print(html_time)
        #print(html_content)
        with codecs.open(out_html, 'w', 'utf-8') as f:
                for ndx, seg in enumerate(seg_order):
                        f.write(u'{}\n\n'.format(html_time[ndx]))

                        if len(html_content[ndx]) == 0:
                                if len(seg_content[seg]) > 0:
                                        output = ['<p>']
                                        for token in seg_content[seg]:
                                                if not token[1].startswith(u"<") and not token[1].endswith(u">"):
                                                    if token[2] > 0.8:
                                                            output.append('<time datetime="{}">{}<time>'.format(token[0], token[1]))
                                                    elif token[2] > 0.4:
                                                            output.append('<time datetime="{}"><conf style="background-color: #FFA500">{}</conf></time>'.format(token[0], token[1]))
                                                    else:
                                                            output.append('<time datetime="{}"><conf style="background-color: #FF0000">{}</conf></time>'.format(token[0], token[1]))

                                        output.append('</p>')
                                        f.write('{}\n\n'.format(' '.join(output)))
                                else:
                                        f.write(u'<p><span style="color: #FF0000;">Sorry could not recognise this audio section!</span></p>\n\n')
                        else:
                                f.write(u'{}\n'.format(html_content[ndx]))

