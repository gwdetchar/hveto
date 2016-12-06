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

import os.path
from math import ceil

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'


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


def omega_scan_complete(scandir):
    """Determine whether an omega scan was completed in the given directory

    Parameters
    ----------
    scandir : `str`
        output directory for a single omega scan

    Returns
    -------
    complete : `bool`
        `True` if the scan is considered complete, otherwise `False`

    Notes
    -----
    The test is whether the final line of the `log.txt` file in the `scandir`
    starts with 'finished on'.
    """
    logfile = os.path.join(scandir, 'log.txt')
    try:
        with open(logfile) as f:
            f.seek(-2, 2)
            while f.read(1) != b'\n':
                f.seek(-2, 1)
            line = f.readline()
    except IOError:
        return False
    else:
        if line.startswith('finished on '):
            return True
    return False
