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

from math import ceil

from gwdatafind.utils import filename_metadata

__author__ = 'Duncan Macleod <duncan.macleod@ligo.org>'
__credits__ = 'Alex Urban <alexander.urban@ligo.org>'


def write_lal_cache(target, paths):
    # if not an open file, open it
    if isinstance(target, str):
        with open(target, "w") as fobj:
            write_lal_cache(fobj, paths)
            return target

    # write to file
    for path in paths:
        obs, tag, segment = filename_metadata(path)
        print(obs, tag, segment[0], abs(segment), path, file=target)

    return target


# -- utilities ----------------------------------------------------------------

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
