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

"""Trigger I/O utilities for hveto
"""

import glob
import os.path
import re

from numpy.lib import recfunctions

from glue.lal import Cache

from gwpy.table import lsctables
from gwpy.table.io import trigfind

TABLE = {
    'omicron': lsctables.SnglBurstTable,
}

def get_triggers(channel, etg, segments, cache=None, snr=None, frange=None,
                 columns=None):
    """Get triggers for the given channel
    """
    Table = TABLE[etg.lower()]
    if columns is None and issubclass(Table, lsctables.SnglInspiralTable):
        columns = ['end_time', 'end_time_ns', 'snr', 'chisq', 'chisq_dof',
                   'mchirp']
    elif columns is None and issubclass(Table, lsctables.SnglBurstTable):
        columns = ['peak_time', 'peak_time_ns', 'snr', 'peak_frequency']

    # find triggers
    if cache is None:
        cache = Cache()
        for start, end in segments:
            cache.extend(trigfind.find_trigger_urls(channel, etg, start, end))
    # read cache
    trigs = lsctables.New(Table, columns=columns)
    for segment in segments:
        if len(cache.sieve(segment=segment)):
            filt = lambda t: float(t.get_peak()) in segment
            trigs.extend(Table.read(cache.sieve(segment=segment), filt=filt))
    recarray = trigs.to_recarray(columns=columns)
    # rename columns for convenience later
    if issubclass(Table, lsctables.SnglInspiralTable):
        tcols = ['end_time', 'end_time_ns']
    elif issubclass(Table, lsctables.SnglBurstTable):
        tcols = ['peak_time', 'peak_time_ns']
        recarray = recfunctions.rename_fields(
            recarray, {'peak_frequency': 'frequency'})
    else:
        tcols = None
    if tcols:
        times = recarray[tcols[0]] + recarray[tcols[1]] * 1e-9
        recarray = recfunctions.rec_append_fields(
            recarray, 'time', times, times.dtype)
        recarray = recfunctions.rec_drop_fields(recarray, tcols)
    # filter
    if snr is not None:
        recarray = recarray[recarray['snr'] >= snr]
    if frange is not None:
        recarray = recarray[
            (recarray['frequency'] >= frange[0]) &
            (recarray['frequency'] < frange[1])]
    return recarray


re_delim = re.compile('[_-]')

def find_auxiliary_channels(etg, gps='*', ifo='*'):
    """Find all auxiliary channels processed by a given ETG
    """
    channels = glob.glob(os.path.join(
        trigfind.TRIGFIND_BASE_PATH, '*', ifo, '*', str(gps)[:5]))
    out = set()
    stub = '_%s' % etg.lower()
    for path in channels:
        path = os.path.split(path)[0]
        if not path.lower().endswith('_%s' % etg.lower()):
            continue
        ifo, name = path[:-len(stub)].rsplit(os.path.sep)[-2:]
        out.add('%s:%s' % (ifo, name))
    return sorted(out)
