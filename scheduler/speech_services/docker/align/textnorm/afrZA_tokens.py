#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This defines the token matchers and expansion functions for
   Afrikaans.  Expansions are returned as list of word lists. Returned
   words should be in lowercase.
    
   Possible TODO:
     - Revise re expressions to use Unicode-aware classes
"""
from __future__ import unicode_literals, division, print_function #Py2

__author__ = "Daniel van Niekerk"
__email__ = "dvn.demitasse@gmail.com"

import os
import sys
debug = sys.stderr #open("/dev/null", "wb")
import re
import codecs
import itertools

from afrZA_numexp import expand as num_expand1
from afrZA_numexp import _expand as num_expand2
from afrZA_numexp import ordinal as ord_expand

TEXTNORM_ROOT_DIR = os.getenv("TEXTNORM_ROOT")
SPECIAL_DICT_FILE = os.path.join(TEXTNORM_ROOT_DIR, "data", "afrZA", "g2p.specialdict.txt")
ABBREVS_FILE = os.path.join(TEXTNORM_ROOT_DIR, "data", "afrZA", "norm.abbrev.json")
VALID_GRAPHS_FILE = os.path.join(TEXTNORM_ROOT_DIR, "data", "afrZA", "norm.graphset.txt")

def num_expand(n):
    return [num_expand1(n), num_expand2(n)]

#Punctuation expected around tokens and lowercase Afrikaans graphemes
VALID_PUNCTS = '".,:;!?(){}[]-'
with codecs.open(VALID_GRAPHS_FILE, encoding="utf-8") as infh:
    valid_lower_graphs = "".join(infh.read().split())
    VALID_GRAPHS = "".join(sorted(set(valid_lower_graphs + valid_lower_graphs.upper())))
UNPRONOUNCED = "^\s{}".format(VALID_GRAPHS)
UNPRONOUNCED_DIGITS = "^\d\s{}".format(VALID_GRAPHS)

#All patts will be followed by whitespace or end of line with possible UNPRONOUNCED inbetween (e.g. punctuation)
TOKEND = r"[{}]*(?:\s+|$)".format(UNPRONOUNCED_DIGITS)
#These patterns should not consume starting whitespace!
TOKSTART = r"(?!\s)[{}]*".format(UNPRONOUNCED_DIGITS)

#Translation table for non-standard punct characters
punct_transtable_inchars = "–”“’‘`"
punct_transtable_outchars = "-\"\"'''"
PUNCT_TRANSTABLE = dict((ord(inchar), ord(outchar))
                        for inchar, outchar
                        in zip(punct_transtable_inchars, punct_transtable_outchars))

#Remove non-g2p-able diacritics
DIACRITIC_TRANSTABLE = dict((ord(inchar), ord(outchar))
                            for inchar, outchar
                            in zip("àèìòùáéíóú", "aeiouaeiou"))

def norm(s):
    """lowercase and remove specific diacritics
    """
    return s.lower().translate(DIACRITIC_TRANSTABLE)


############################## GENERAL ##############################

patts_general = [r"(?P<general>(?:[{}]+[{}]*)+)".format(VALID_GRAPHS, UNPRONOUNCED)]
match_general = [TOKSTART + patt + TOKEND for patt in patts_general]

def expand_general(m):
    tokentext = m.group("general")
    print("expand_general():", m.groups(), tokentext.encode("utf-8"), file=debug)
    #We look for subtokens
    subtoks = [e for e in re.split("[{}]".format(UNPRONOUNCED), tokentext) if e != ""]
    if len(subtoks) > 1:
        subexpansions = []
        for subtok in subtoks:
            subexpansions.append([])
            for toktype, patts in TOKEN_PATTERNS.items():
                for patt in patts:
                    pattre = re.compile("^" + patt + "$", flags=re.UNICODE)
                    for tokmatch in pattre.finditer(subtok):
                        print("\t", end="", file=debug)
                        subexpansions[-1].extend(TOKEN_EXPANDERS[toktype](tokmatch))
        expansions = []
        for expansion in itertools.product(*tuple(subexpansions)):
            expansions.append([])
            for e in expansion:
                expansions[-1].extend(e)
            print("\t", expansions, file=debug) 
        return expansions
    else:
        return [[norm(subtoks[0])]]

############################## DATES ##############################

compact_dates = {"delim": "\s*[-/\.\\\\]+\s*",
                 "year": "(?P<year>[0-9]{2,4})",
                 "month": "(?P<month>[0-9]{1,2})",
                 "day": "(?P<day>[0-9]{1,2})"}

writ_month = "Jan|Feb|Mrt|Apr|Mei|Jun|Jul|Aug|Sep|Okt|Nov|Des|Januarie|Februarie|Maart|April|Mei|Junie|Julie|Augustus|September|Oktober|November|Desember"
writ_month = "|".join([writ_month, writ_month.lower()])
writ_daysuf = "nde|de|ste"

writ_dates = {"day": "(?P<day>[0-9]{1,2})(?:%s)?" % writ_daysuf,
              "month": "(?P<month>%s)" % writ_month,
              "year": "(?P<year>[0-9]{4})"}

patts_dates =  [r"{year}{delim}{month}{delim}{day}".format(**compact_dates),
                r"{day}{delim}{month}{delim}{year}".format(**compact_dates),
                r"{month}{delim}{day}{delim}{year}".format(**compact_dates),
                r"{day}\s+(?:van\s+)?{month}[\.,]*\s+{year}".format(**writ_dates),
                r"{month}[\.]?\s+{day}[,]?\s+{year}".format(**writ_dates),
                r"{month}[\.]?\s+{day}".format(day=writ_dates["day"], month=writ_dates["month"]),
                r"{day}\s+(?:van\s+)?{month}".format(day=writ_dates["day"], month=writ_dates["month"])]

match_dates = [TOKSTART + patt + TOKEND for patt in patts_dates]

months = {1: "januarie",
          2: "februarie",
          3: "maart",
          4: "april",
          5: "mei",
          6: "junie",
          7: "julie",
          8: "augustus",
          9: "september",
          10: "oktober",
          11: "november",
          12: "desember"}

monthabbr = {"jan": "januarie",
             "feb": "februarie",
             "mrt": "maart",
             "apr": "april",
             "mei": "mei",
             "jun": "junie",
             "jul": "julie",
             "aug": "augustus",
             "sep": "september",
             "okt": "oktober",
             "nov": "november",
             "des": "desember"}

exppatts_dates = ["{day} {month} {year}",
                  "die {day} {month} {year}",
                  "{month} {day} {year}"]

dayexpand = dict((n, ord_expand(n)) for n in range(1, 32))

def expand_month(month):
    try:
        return months[int(month)]
    except ValueError:
        pass
    except KeyError:
        raise
    try:
        return monthabbr[norm(month)]
    except KeyError:
        pass
    return norm(month)
    

def expand_dates(m):
    print("expand_dates():", m.groups(), file=debug)
    #VALIDATE/INTERPRET MATCH
    try:
        year = int(m.group("year"))
        if year < 100:
            year = 2000 + year
    except IndexError:
        year = None
    try:
        month = expand_month(m.group("month"))
    except KeyError:
        return []
    day = int(m.group("day"))
    if day > 31:
        return []
    #COLLECT ALTERNATIVES
    years = []
    months = []
    days = []
    if year is not None:
        years.extend(num_expand(year))
        years.append(" ".join([num_expand1(int(str(year)[:2])), num_expand1(int(str(year)[2:]))]))
        if str(year)[2:].startswith("0"):
            years.append(" ".join([num_expand1(int(str(year)[:2])), "nul", num_expand1(int(str(year)[2:]))]))
    else:
        years.append("")
    months.append(month)
    days.append(num_expand1(day))
    days.append(dayexpand[day])
    #CONSTRUCT EXPANSIONS
    expansions = []
    for patt in exppatts_dates:
        for year in years:
            for month in months:
                for day in days:
                    expansions.append(patt.format(day=day, month=month, year=year).split())
    return expansions

############################## YEARS ##############################

patts_years = [r"(?P<year>[0-9]{4})"]
match_years = [TOKSTART + patt + TOKEND for patt in patts_years]

def expand_years(m):
    year = int(m.group("year"))
    years = []
    years.append(" ".join([num_expand1(int(str(year)[:2])), num_expand1(int(str(year)[2:]))]))
    if str(year)[2:].startswith("0"):
        years.append(" ".join([num_expand1(int(str(year)[:2])), "nul", num_expand1(int(str(year)[2:]))]))
    expansions = []
    for year in years:
        expansions.append(year.split())
    return expansions

############################## SPELL-OUT ##############################

import string
import unicodedata

with codecs.open(SPECIAL_DICT_FILE, encoding="utf-8") as infh:
    chardict = dict([(line.split()[0], " ".join(line.split()[1:])) for line in infh if line.strip() != ""])

patts_spell = [r"(?P<spell>[0-9A-Z{}]+)".format(re.escape(string.punctuation))]
match_spell = [TOKSTART + patt + TOKEND for patt in patts_spell]

def _expand_spell(tokentext):
    l = []
    for i, c in enumerate(tokentext.lower()):
        cword = "char_" + "_".join(unicodedata.name(c).lower().split())
        if cword in chardict: #spell-out limited by what has been defined in pronundict
            l.append(cword)
    return l

def expand_spell(m):
    #remove possible enveloping punctuation
    tokentext = re.sub("^[{punct}]*([0-9A-Z]+)[{punct}]*$".format(punct=re.escape(VALID_PUNCTS)), "\\1", m.group("spell"))
    print("expand_spell():", m.groups(), tokentext.encode("utf-8"), file=debug)
    return [_expand_spell(tokentext)]

############################## SPELL PLURAL ##############################
## DEMITASSE: Merge this case into "spell" class

patts_spellplural = [r"(?P<spellplural>[0-9A-Z{}]+)'?s".format(re.escape(string.punctuation))]
match_spellplural = [TOKSTART + patt + TOKEND for patt in patts_spellplural]

def _expand_spellplural(tokentext):
    l = _expand_spell(tokentext)
    l.append("plural_phoneme")
    return l

def expand_spellplural(m):
    #remove possible enveloping punctuation
    tokentext = re.sub("^[{punct}]*([0-9A-Z]+)[{punct}]*$".format(punct=re.escape(VALID_PUNCTS)), "\\1", m.group("spellplural"))
    print("expand_spellplural():", m.groups(), tokentext.encode("utf-8"), file=debug)
    return [_expand_spellplural(tokentext)]


############################## TIMES ##############################

compact_times = {"delim": "\s*[:;\-hH]\s*",
                 "hour": "(?P<hour>[0-9]{1,2})",
                 "minute": "(?P<minute>[0-9]{2})",
                 "noon": "(?P<noon>\s[vVnN][\.]?[mM][\.]?)*"}

patts_times = [#r"{hour}{delim}{minute}".format(**compact_times),
               r"{hour}{delim}{minute}{noon}".format(**compact_times)]
match_times = [TOKSTART + patt + TOKEND for patt in patts_times]


def expand_noon(hour, minute, afternoon):
    if hour == 12 and minute == 0:
        noon = ["", "middag"]
    elif hour == 0 and minute == 0:
        noon = ["", "middernag"]
    else:
        noon = [""]
    if afternoon:
        noon.extend(["namiddag",
                     "in die middag",
                     "in die aand",
                     " ".join(_expand_spell("nm"))])
    else:
        noon.extend(["voormiddag",
                     "in die oggend",
                     " ".join(_expand_spell("vm"))])
    return noon
    
exppatts_mtoh = [r"{minute} minute voor {hour} {noon}",
                    r"{minute} voor {hour} {noon}"]
exppatts_mpasth = [r"{minute} minute na {hour} {noon}",
                      r"{minute} minute oor {hour} {noon}",
                      r"{minute} na {hour} {noon}",
                      r"{minute} oor {hour} {noon}"]
exppatts_hm = [r"{hour} {minute} {noon}"]
exppatts_24 = [r"{hour} {delim} {minute}"]
expdelim24 = ["honderd",
              "honderd uur",
              ""]

def expand_specialtimes(hour, minute, afternoon):
    expansions = []
    for noon in expand_noon(hour, minute, afternoon):
        if minute == 0:
            expansions.extend(["{hour} uur {noon}".format(hour=num_expand1(hour % 12 or 12), noon=noon),
                               "{hour} {noon}".format(hour=num_expand1(hour % 12 or 12), noon=noon)])
        elif minute == 30:
            expansions.append("half {hour} {noon}".format(hour=num_expand1((hour+1) % 12 or 12), noon=noon))
        elif minute == 15:
            expansions.append("kwart oor {hour} {noon}".format(hour=num_expand1(hour % 12 or 12), noon=noon))
        elif minute == 15:
            expansions.append("kwart voor {hour} {noon}".format(hour=num_expand1((hour+1) % 12 or 12), noon=noon))
    return expansions

def expand_24hrtimes(hour, minute, afternoon):
    if afternoon and hour < 12:
        hour += 12
    elif not afternoon:
        hour = hour % 12 or 12
    if minute == 0:
        minutes = [""]
    elif minute < 10:
        minutes = ["nul {}".format(num_expand1(minute))]
    else:
        minutes = [num_expand1(minute)]
    hours = [num_expand1(hour)]
    expansions = []
    for patt in exppatts_24:
        for hr in hours:
            for mn in minutes:
                for delim in expdelim24:
                    expansions.append(patt.format(hour=hr, delim=delim, minute=mn))
    return expansions

def expand_times(m):
    #DEMITASSE: TODO: Simplify this... reduce repetition
    hour = int(m.group("hour"))
    hour2 = hour + 1
    minute = int(m.group("minute"))
    minute2 = 60 - minute
    try:
        afternoon = "p" in m.group("noon").lower()
    except AttributeError:
        afternoon = hour >= 12
    print("expand_times():", m.groups(), file=debug)
    expansions = []
    if minute == 0:
        expansions.extend(expand_specialtimes(hour, minute, afternoon))
    else:
        #COLLECT "minutes past" expansions
        hours = [hour]
        minutes = [minute]
        noons = expand_noon(hour, minute, afternoon) #also returns empty string ("not pronounced")
        for patt in exppatts_mpasth:
            for hr in hours:
                for mn in minutes:
                    for noon in noons:
                        expansions.append(patt.format(hour=num_expand1(hr % 12 or 12),
                                                      minute=num_expand1(mn),
                                                      noon=noon))
        #COLLECT "minutes to" expansions
        hours = [hour2]
        minutes = [minute2]
        noons = noons
        for patt in exppatts_mtoh:
            for hr in hours:
                for mn in minutes:
                    for noon in noons:
                        expansions.append(patt.format(hour=num_expand1(hr % 12 or 12),
                                                      minute=num_expand1(mn),
                                                      noon=noon))
        #COLLECT "hour minute"
        hours = [hour]
        minutes = [minute]
        noons = noons
        for patt in exppatts_hm:
            for hr in hours:
                for mn in minutes:
                    for noon in noons:
                        expansions.append(patt.format(hour=num_expand1(hr % 12 or 12),
                                                      minute=num_expand1(mn),
                                                      noon=noon))
        #COLLECT "special case"
        if minute in [15, 30, 45]:
            expansions.extend(expand_specialtimes(hour, minute, afternoon))
    #COLLECT "24 hour"
    expansions.extend(expand_24hrtimes(hour, minute, afternoon))
    expansions = [e.split() for e in set(expansions)]
    return expansions


############################## CARDINALS ##############################

patts_crds = [r"(?P<digits>\d+)"]
match_crds = [TOKSTART + patt + TOKEND for patt in patts_crds]

def expand_crds(m):
    tokentext = m.group("digits")
    print("expand_crds():", m.groups(), tokentext.encode("utf-8"), file=debug)
    return [t.split() for t in num_expand(int(tokentext))]

############################## CARDINALSUFF ##############################

patts_crdsuff = [r"(?P<digits>\d+)(?P<suff>[{}]+)".format(VALID_GRAPHS)]
match_crdsuff = [TOKSTART + patt + TOKEND for patt in patts_crdsuff]

def expand_crdsuff(m):
    digits = m.group("digits")
    suff = m.group("suff")
    print("expand_crdsuff():", m.groups(), digits.encode("utf-8"), suff.encode("utf-8"), file=debug)
    #DEMIT
    return [t.split() for t in num_expand(int(digits))]

############################## ORDINALS ##############################

ord_suff = writ_daysuf

patts_ords = [r"(?P<digits>\d+)({})".format(ord_suff)]
match_ords = [TOKSTART + patt + TOKEND for patt in patts_ords]

def expand_ords(m):
    tokentext = m.group("digits")
    print("expand_ords():", m.groups(), tokentext.encode("utf-8"), file=debug)
    return [ord_expand(int(tokentext)).split()]


############################## FLOATS ##############################

patts_floats = [r"(?P<float>\d+\.\d+)"]
match_floats = [TOKSTART + patt + TOKEND for patt in patts_floats]

def expand_floats(m):
    tokentext = m.group("float")
    print("expand_floats():", m.groups(), tokentext.encode("utf-8"), file=debug)    
    w = []
    for c in tokentext:
        if c == ".":
            w.append("punt")
        else:
            try:
                w.append(num_expand1(int(c)))
            except ValueError:
                w.append(_expand_spell(c)) #shouldn't happen
    return [w]


############################## SECTIONS ##############################

patts_sections = [r"(?P<section>\d+(:?\.\d+)+)"]
match_sections = [TOKSTART + patt + TOKEND for patt in patts_sections]

def expand_sections(m):
    tokentext = m.group("section")
    print("expand_sections():", m.groups(), tokentext.encode("utf-8"), file=debug)    
    w = []
    for tok in tokentext.split(".")[:-1]:
        w.extend(num_expand1(int(tok)).split())
        w.append("punt")
    w.extend(num_expand1(int(tokentext.split(".")[-1])).split())
    return [w]


############################## CURRENCY ##############################

patts_curr = [r"(?P<denom>A\$|a\$|NZ\$|nz\$|\$|R|r|£|¥|€)\s*(?P<curr>[0-9]+)(?:\.(?P<cent>[0-9]{2}))?",
              r"(?P<denom>A\$|a\$|NZ\$|nz\$|\$|R|r|£|¥|€)\s*(?P<curr>[0-9]+(?:\.[0-9]+)?)\s*(?P<mult>mil|mn|mln|bil|bn|bln|tril|tn|trn|trln|mlrd|blrd)"]
match_curr = [TOKSTART + patt + TOKEND for patt in patts_curr]

denom_map_curr = {"r": "rand",
                  "$": "dollar",
                  "£": "pond",
                  "€": "euro",
                  "¥": "yen",
                  "₨": "rupee",
                  "a$": "australiaanse dollar",
                  "nz$": "nieu seelandse dollar"}

mult_map_curr = {"m": "miljoen",
                 "b": "biljoen",
                 "t": "triljoen"}

mult_template = ["{curr} {mult} {denom}"]
cent_template = ["{curr} {denom} {cent}"]

def expand_curr(m):
    print("expand_currency():", m.groups(), file=debug)
    expansions = []
    if not "mult" in m.groupdict():
        denom = m.group("denom").lower()
        curr = int(m.group("curr"))
        cent = m.group("cent") #can be None
        denoms = [denom_map_curr[denom]]
        currs = num_expand(curr)
        cents = []
        if cent is not None:
            i = int(cent)
            if i:
                cent = num_expand1(i)
                cents.extend(["en {cent} sent".format(cent=cent),
                              "{cent}".format(cent=cent)])
            else:
                cents.append("")
        else:
            cents.append("")
        for template in cent_template:
            for curr in currs:
                for cent in cents:
                    for denom in denoms:
                        expansions.append(template.format(curr=curr,
                                                          denom=denom,
                                                          cent=cent))
    else:
        denom = m.group("denom").lower()
        curr = m.group("curr")
        mult = mult_map_curr[m.group("mult")[0]]
        denoms = [denom_map_curr[denom],
                  denom_map_curr[denom] + "s"]
        print(num_expand1(int(curr.split(".")[0])), file=debug)
        print(_expand_spell(curr.split(".")[1])[0], file=debug)
        
        currs = [num_expand1(int(curr.split(".")[0])) + " punt " + " ".join(map(lambda x: num_expand1(int(x)), curr.split(".")[-1]))]
        for template in mult_template:
            for curr in currs:
                for denom in denoms:
                    expansions.append(template.format(curr=curr,
                                                      denom=denom,
                                                      mult=mult))
    expansions = [e.split() for e in set(expansions)]
    print(expansions, file=debug)
    return expansions

############################## ABBREVIATIONS ##############################

import json

with codecs.open(ABBREVS_FILE, encoding="utf-8") as infh:
    abbreviations = json.load(infh)
#print(abbreviations, file=debug)
    
patts_abbrev = ["(?P<abbrev>{})".format("|".join(abbreviations))]
match_abbrev = [TOKSTART + patt + TOKEND for patt in patts_abbrev]

def expand_abbrev(m):
    print("expand_abbrev():", m.groups(), file=debug)
    expansions = [expansion.lower().split() for expansion in abbreviations[m.group("abbrev")]]
    print("\t", expansions, file=debug)
    return expansions

############################## DEFS ##############################

TOKEN_PATTERNS = {"general": patts_general,
                  "date": patts_dates,
                  "year": patts_years,
                  "spell": patts_spell,
                  "spellplural": patts_spellplural,
                  "time": patts_times,
                  "cardinal": patts_crds,
                  "cardinalsuff": patts_crdsuff,
                  "ordinal": patts_ords,
                  "floats": patts_floats,
                  "sections": patts_sections,
                  "currency": patts_curr,
                  "abbreviations": patts_abbrev}
TOKEN_MATCHERS = {"general": match_general,
                  "date": match_dates,
                  "year": match_years,
                  "spell": match_spell,
                  "spellplural": match_spellplural,
                  "time": match_times,
                  "cardinal": match_crds,
                  "cardinalsuff": match_crdsuff,
                  "ordinal": match_ords,
                  "floats": match_floats,
                  "sections": match_sections,
                  "currency": match_curr,
                  "abbreviations": match_abbrev}
TOKEN_EXPANDERS = {"general": expand_general,
                   "date": expand_dates,
                   "year": expand_years,
                   "spell": expand_spell,
                   "spellplural": expand_spellplural,
                   "time": expand_times,
                   "cardinal": expand_crds,
                   "cardinalsuff": expand_crdsuff,
                   "ordinal": expand_ords,
                   "floats": expand_floats,
                   "sections": expand_sections,
                   "currency": expand_curr,
                   "abbreviations": expand_abbrev}
