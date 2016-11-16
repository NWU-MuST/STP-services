#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Number expansion for the English language...
"""
from __future__ import unicode_literals, division, print_function #Py2

__author__ = "Daniel van Niekerk"
__email__ = "dvn.demitasse@gmail.com"

import re

patterns1 = {0: ["zero"],
             1: ["one"],
             2: ["two"],
             3: ["three"],
             4: ["four"],
             5: ["five"],
             6: ["six"],
             7: ["seven"],
             8: ["eight"],
             9: ["nine"],
             10: ["ten"],
             11: ["eleven"],
             12: ["twelve"],
             13: ["thirteen"],
             14: ["fourteen"],
             15: ["fifteen"],
             16: ["sixteen"],
             17: ["seventeen"],
             18: ["eighteen"],
             19: ["nineteen"],
             20: ["twenty", "twenty %(mod)s"],
             30: ["thirty", "thirty %(mod)s"],
             40: ["forty", "forty %(mod)s"],
             50: ["fifty", "fifty %(mod)s"],
             60: ["sixty", "sixty %(mod)s"],
             70: ["seventy", "seventy %(mod)s"],
             80: ["eighty", "eighty %(mod)s"],
             90: ["ninety", "ninety %(mod)s"],
             100: ["%(div)s hundred", "%(div)s hundred and %(mod)s"],
             1000: ["%(div)s thousand", "%(div)s thousand %(mod)s"],
             1000000: ["%(div)s million", "%(div)s million %(mod)s"],
             1000000000: ["%(div)s billion", "%(div)s billion %(mod)s"],             
             1000000000000: ["%(div)s trillion", "%(div)s trillion %(mod)s"]
            }

def _expand(n):
    patterns = patterns1
    if n <= 1:
        return patterns[n][0]
    for pn in reversed(sorted(patterns)):
        modt = ""
        divt = ""
        d = n // pn
        if d == 0:
            continue
        m = n % pn
        if m > 0:
            modt = _expand(m)
            t = patterns[pn][1]
        else:
            t = patterns[pn][0]
        divt = _expand(d)
        return t % {"div": divt, "mod": modt}

def expand(n):
    """This one adds 'and' in certain places...
    """
    s = _expand(n)
    bignums = ["thousand", "million", "billion", "trillion"]
    smallnums = [patterns1[n][0] for n in range(1, 20)]
    midnums = [patterns1[n*10][0] for n in range(2, 10)]
    s = re.sub("(%s)\s((?:%s)?\s?(?:%s))$" % ("|".join(bignums), "|".join(midnums), "|".join(smallnums)), "\\1 and \\2", s)
    return s

### FROM: http://halley.cc/code/?python/english.py

__score = [ 'zero', 'one', 'two', 'three', 'four', 'five', 'six',
            'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve',
            'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen',
            'eighteen', 'nineteen' ]

__decade = [ 'zero', 'ten', 'twenty', 'thirty', 'forty', 'fifty',
             'sixty', 'seventy', 'eighty', 'ninety', 'hundred' ]

__groups = [ 'zero', 'thousand', 'million', 'billion',
             # 'trillion',
             # 'quadrillion', 'quintillion', 'sextillion', 'septillion',
             # 'octillion', 'nonillion'
             ]

__groupvalues = [ 0, 1000, 1000000, 1000000000,
                  # 1000000000000,
                  # 1000000000000000,
                  # 1000000000000000000,
                  # 1000000000000000000000,
                  # ...
                  ]

def cardinal(number, style=None):
    '''Returns a phrase that spells out the cardinal form of a number.
    This routine does not currently try to understand "big integer"
    numbers using words like 'septillion'.
    '''
    if not number:
        return __score[0]
    text = ''
    if number < 0:
        text = 'negative '
        number = -number
    for group in reversed( range( len(__groups) ) ):
        if not group: continue
        if number >= __groupvalues[group]:
            multiple = int(number / __groupvalues[group])
            text += cardinal(multiple) + ' ' + __groups[group]
            number %= __groupvalues[group]
            if number:
                text += ' ' #used to be ', '
    if number >= 100:
        text += cardinal(int(number / 100)) + ' ' + __decade[10]
        number %= 100
        if number:
            text += ' '
    if number >= 20:
        text += __decade[int(number/10)]
        number %= 10
        if number:
            text += ' ' #used to be '-'
    if number > 0:
        text += __score[number]
    return text

__scoreth = [ 'zeroth', 'first', 'second', 'third', 'fourth', 'fifth',
              'sixth', 'seventh', 'eighth', 'ninth', 'tenth',
              'eleventh', 'twelfth', 'thirteenth', 'fourteenth',
              'fifteenth', 'sixteenth', 'seventeenth', 'eighteenth',
              'nineteenth' ]

__decadeth = [ 'zeroth', 'tenth', 'twentieth', 'thirtieth', 'fortieth',
               'fiftieth', 'sixtieth', 'seventieth', 'eightieth',
               'ninetieth', 'hundredth' ]

def ordinal(number, style=None):
    '''Returns a phrase that spells out the ordinal form of a number.'''
    if not number:
        return __scoreth[0]
    text = ''
    if number < 0:
        text = 'negative '
        number = -number
    if number >= 100:
        text += cardinal(number - (number % 100))
        if (number % 1000) > 0 and (number % 1000) - (number % 100) == 0:
            text += ''#used to be ','
        number %= 100
        if number:
            text += ' '
    if not number:
        return text + 'th'
    if number >= 20:
        spare = number % 10
        if not spare:
            text += __decadeth[int(number/10)]
        else:
            text += __decade[int(number/10)] + ' ' #used to be '-'
        number = spare
    if number > 0:
        text += __scoreth[number]
    return text





if __name__ == "__main__":
    import os, sys
    print(expand(int(sys.argv[1])))
    print(ordinal(int(sys.argv[1])))
