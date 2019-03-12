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

"""Segment utilities for hveto
"""

from __future__ import print_function

import os
import os.path
from functools import wraps

try:
    from urllib.parse import urlparse
    from urllib.request import urlopen
except ImportError:  # python < 3
    from urlparse import urlparse
    from urllib2 import urlopen

from gwpy.segments import (DataQualityFlag, DataQualityDict)

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Joshua Smith <joshua.smith@ligo.org>'

DEFAULT_SEGMENT_SERVER = os.getenv('DEFAULT_SEGMENT_SERVER',
                                   'https://segments.ligo.org')


def integer_segments(f):
    @wraps(f)
    def decorated_method(*args, **kwargs):
        flag = f(*args, **kwargs)
        segs = flag.active
        flag.active = type(segs)(type(s)(int(s[0]), int(s[1])) for s in segs)
        return flag
    return decorated_method


@integer_segments
def query(flag, start, end, url=DEFAULT_SEGMENT_SERVER):
    """Query a segment database for active segments associated with a flag
    """
    return DataQualityFlag.query(flag, start, end, url=url)


def write_ascii(outfile, segmentlist, ncol=4):
    if ncol not in [2, 4]:
        raise ValueError("Invalid number of columns: %r" % ncol)
    with open(outfile, 'w') as f:
        for i, seg in enumerate(segmentlist):
            if ncol == 2:
                print("%f %f" % seg, file=f)
            else:
                print("%d\t%f\t%f\t%f" % (i, seg[0], seg[1], abs(seg)), file=f)


def read_veto_definer_file(vetofile, start=None, end=None, ifo=None):
    """Read a veto definer file, downloading it if necessary
    """
    if urlparse(vetofile).netloc:
        tmp = urlopen(vetofile)
        vetofile = os.path.abspath(os.path.basename(vetofile))
        with open(vetofile, 'w') as f:
            f.write(str(tmp.read()))
    return DataQualityDict.from_veto_definer_file(
        vetofile, format='ligolw', start=start, end=end, ifo=ifo)
