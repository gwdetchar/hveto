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

import glob
import warnings

from hveto import const

from math import ceil

from gwdatafind.utils import filename_metadata

from gwpy.table import EventTable, Column

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


def primary_vetoed(starttime=None, hveto_path=None, snr=6.0,
                   significance=5.0):

    """Catalogue all vetoed primary triggers from a given analysis

    This utility queries the output of an hveto analysis for the triggers
    vetoed from its primary channel over all rounds (up to thresholds on
    signal-to-noise ratio and round significance).

    Parameters
    ----------
    start, end : `str` or `float`
        start and end GPS times for this analysis

    ifo : `str`
        string denoting the interferometer, e.g. ``'H1'`` for Hanford

    snr : `float`, optional
        signal-to-noise ratio threshold on triggers, default: 6.0

    significance : `float`, optional
        hveto significance threshold on auxiliary channels, default: 5.0

    output_dir : `str`, optional
        output directory for data products, default: `'.'`

    Returns
    -------
    catalogue : `~gwpy.table.EventTable`
        a tabular catalogue of which triggers were vetoed from the primary
        channel, and which auxiliary channel caused them to be vetoed"""

    if starttime:
        path = const.get_hvetopath(starttime)
    else:
        path = hveto_path

    t_vetoed = EventTable(names=['time', 'snr', 'peak_frequency', 'channel',
                                 'winner', 'significance'])
    try:
        files = glob.glob(path+'/triggers/' + '/*VETOED*.txt')
        t_summary = EventTable.read(path + '/summary-stats.txt',
                                    format='ascii')
        n = len(t_summary)
        files = files[:n]
        t_vetoed = EventTable.read(files, format='ascii')
        lenoffiles = t_summary['nveto']
        winsig = [round(t_summary['significance'][i], 4) for i in range(n)
                  for j in range(lenoffiles[i])]
        winchans = [t_summary['winner'][i] for i in range(n) for j in
                    range(lenoffiles[i])]
        rounds = [i+1 for i in range(n) for j in range(lenoffiles[i])]
        colsig = Column(data=winsig, name='significance')
        colwin = Column(data=winchans, name='winner')
        colround = Column(data=rounds, name='round')
        t_vetoed.add_column(colwin)
        t_vetoed.add_column(colsig)
        t_vetoed.add_column(colround)
    except (FileNotFoundError, ValueError):
        warnings.warn("Hveto did not run this day")

    return t_vetoed
