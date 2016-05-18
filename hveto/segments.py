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

from functools import wraps

from gwpy.segments import DataQualityFlag, Segment, SegmentList

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Joshua Smith <joshua.smith@ligo.org>'


def integer_segments(f):
    @wraps(f)
    def decorated_method(*args, **kwargs):
        segs = f(*args, **kwargs)
        return type(segs)(type(s)(int(s[0]), int(s[1])) for s in segs)
    return decorated_method


@integer_segments
def query(flag, start, end, url='https://segments.ligo.org'):
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
