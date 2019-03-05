# -*- coding: utf-8 -*-
# Copyright (C) Joshua Smith (2016-)
#
# This file is part of the hveto python package.
#
# hveto is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# hveto is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with hveto.  If not, see <http://www.gnu.org/licenses/>.

"""General utilities for hveto
"""

from __future__ import division

import sys
import os.path
from math import ceil

try:  # python 3.x
    from io import StringIO
    from html.parser import HTMLParser
    from html.entities import name2codepoint
except:  # python 2.7
    from cStringIO import StringIO
    from HTMLParser import HTMLParser
    from htmlentitydefs import name2codepoint

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Alex Urban <alexander.urban@ligo.org>'


# -- class for HTML parsing ---------------------------------------------------

class HvetoHTMLParser(HTMLParser):
    """See https://docs.python.org/3/library/html.parser.html.
    """
    def handle_starttag(self, tag, attrs):
        print("Start tag:", tag)
        attrs.sort()
        for attr in attrs:
            print("attr:", attr)

    def handle_endtag(self, tag):
        print("End tag:", tag)

    def handle_data(self, data):
        print("Data:", data)

    def handle_comment(self, data):
        print("Comment:", data)

    def handle_entityref(self, name):
        c = chr(name2codepoint[name])
        print("Named entity:", c)

    def handle_charref(self, name):
        if name.startswith('x'):
            c = chr(int(name[1:], 16))
        else:
            c = chr(int(name))
        print("Numeric entity:", c)

    def handle_decl(self, data):
        print("Decl:", data)

parser = HvetoHTMLParser()


# -- utilities ----------------------------------------------------------------

def parse_html(html):
    """Parse a string containing raw HTML code
    """
    stdout = sys.stdout
    sys.stdout = StringIO()
    if sys.version_info.major < 3:
        parser.feed(html.decode('utf-8', 'ignore'))
    else:
        parser.feed(html)
    output = sys.stdout.getvalue()
    sys.stdout = stdout
    return output


def channel_groups(channellist, ngroups):
    """Separate a list of channels into a number of equally-sized groups

    Parameters
    ----------
    channellist : `list`
        large list to separate into chunks
    ngroups : `int`
        number of output groups

    Returns
    -------
    iterator : iterator `list` of `list`
        a generator sequence yielding a sub-list on each iteration
    """
    n = int(ceil(len(channellist) / ngroups))
    for i in range(0, len(channellist), n):
        yield channellist[i:i+n]
