#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function #Py2

import sys
import codecs
import os
import re
import wave
import datetime

MIN_SEG = 0.5

if len(sys.argv) != 6:
        print('usage: {} in_wave in_html seg_file inter_file seg_len'.format(sys.argv[0]))
        sys.exit(1)

prog_name, in_wave, in_html, seg_file, inter_file, seg_len = sys.argv

f = wave.open(in_wave, 'rb')
dur = float(f.getnframes()) / float(f.getframerate())
f.close()

data = None
with codecs.open(in_html, 'r', 'utf-8') as f:
        data = f.readlines()
all_data = ''.join(data)

with codecs.open(in_html, 'w', 'utf-8') as f:
        # Check that we have some data
        if len(all_data) == 0 or 'type="mark"' not in all_data:
                #f.write('<p><span style="color: #FF0000;">You must run indexing first!</span></p>\n')
                #f.write(all_data)
                #sys.exit(1)
                data.insert(0, '<p><time type="mark" style="background-color: #AAAAAA;" datetime="0.0">0:0:0</time></p>')

        # Extract segments
        segments = []
        content = {'empty': []}
        seg_name = 'empty'
        time_mark = []
        for line in data:
                if 'type="mark"' in line:
                        match = re.search('datetime="(.+?)"', line)
                        if match is not None:
                                seg_name = match.group(1)
                                segments.append(seg_name)
                                content[seg_name] = []
                                time_mark.append(line.strip(u'\n'))
                        else:
                                seg_name = 'empty'
                        continue

                content[seg_name].append(line.strip('\n'))

        # Missing 0.0 time mark
        if "0.0" not in content:
            segments.insert(0, "0.0")
            time_mark.insert(0, '<p><time type="mark" style="background-color: #AAAAAA;" datetime="0.0">0:0:0</time></p>') 
            content["0.0"] = u""

        # Remove "empty" text segments
        for seg_name in segments:
                text = ''.join(content[seg_name])
                text = re.sub('<p>&nbsp;</p>', '', text)
                if len(text) == 0:
                        content[seg_name] = ''

        segments.append(str(dur))
        out_seg = []
        with codecs.open(inter_file, 'w', 'utf-8') as fint:

                for ndx in range(len(segments)-1):
                        f.write(u'<p><time type="mark" style="background-color: #AAAAAA;" datetime="{}">{}</p>\n'.format(float(segments[ndx]),datetime.timedelta(seconds=int(float(segments[ndx])))))

                        if content[segments[ndx]] != '':
                                f.write(u'\n'.join(content[segments[ndx]]))
                                fint.write(u'{}#$%'.format(time_mark[ndx]))
                                fint.write(u'{}\n'.format(u'#$%'.join(content[segments[ndx]])))
                        else:
                                if (float(segments[ndx+1]) - float(segments[ndx])) > float(seg_len):
                                        f.write(u'<p><span style=""color: #FF0000;">This segment is too long for recognition -- 5 min limit per segment!<br>Please break it up using insert time mark.</span></p>\n')
                                        fint.write(u'{}#$%'.format(time_mark[ndx]))
                                        fint.write(u'<p><span style=""color: #FF0000;">This segment is too long for recognition -- 5 min limit per segment!<br>Please break it up using insert time mark.</span></p>\n')
                                elif (float(segments[ndx+1]) - float(segments[ndx])) < float(MIN_SEG):
                                        f.write(u'<p><span style=""color: #FF0000;">This segment is too short for recognition -- must be longer than 0.5 seconds!<br>Please merge this segment.</span></p>\n')
                                        fint.write(u'{}#$%'.format(time_mark[ndx]))
                                        fint.write(u'<p><span style=""color: #FF0000;">This segment is too short for recognition -- must be longer than 0.5 seconds!<br>Please merge this segment.</span></p>\n')
                                else:
                                        f.write(u'<p>&nbsp;</p>\n')
                                        fint.write(u'{}#$%'.format(time_mark[ndx]))
                                        fint.write(u'\n')
                                        out_seg.append((float(segments[ndx]), float(segments[ndx+1])))

        with codecs.open(seg_file, 'w', 'utf-8') as fseg:
                for ndx, line in enumerate(out_seg):
                        start, end = line
                        print(start, end)
                        if ndx == 0 and start != 0.0:
                            fseg.write('sil\t0.00\t{:.2f}\n'.format(start))
                        if ndx > 0:
                                if int(out_seg[ndx-1][1]) != int(out_seg[ndx][0]):
                                    fseg.write('sil\t{:.2f}\t{:.2f}\n'.format(out_seg[ndx-1][1], out_seg[ndx][0]))
                        fseg.write('speech\t{:.2f}\t{:.2f}\n'.format(start, end))

                        if ndx+1 == len(out_seg):
                                if int(end) != int(dur):
                                    fseg.write('sil\t{:.2f}\t{:.2f}\n'.format(end, dur))

