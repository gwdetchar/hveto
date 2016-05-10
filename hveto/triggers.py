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

import numpy
from numpy.lib import recfunctions

from glue.lal import Cache
from glue.ligolw.table import StripTableName as strip_table_name

from gwpy.table import lsctables

try:  # use new trigfind module
    import trigfind
except ImportError:
    from gwpy.table.io import trigfind


TABLE = {
    'omicron': lsctables.SnglBurstTable,
    'daily-cbc': lsctables.SnglInspiralTable,
}

COLUMNS = {
    lsctables.SnglInspiralTable: [
        'end_time', 'end_time_ns', 'mchirp', 'snr'],
    lsctables.SnglBurstTable: [
        'peak_time', 'peak_time_ns', 'peak_frequency', 'snr'],
}


def get_triggers(channel, etg, segments, cache=None, snr=None, frange=None,
                 columns=None, **kwargs):
    """Get triggers for the given channel
    """
    # get table from etg
    Table = TABLE[etg.lower()]
    tablename = strip_table_name(Table.tableName)
    # get default columns for this table
    if columns is None:
        for key in COLUMNS:
            if issubclass(Table, key):
                columns = COLUMNS[key][:]
                break

    # find triggers
    if cache is None:
        cache = Cache()
        for start, end in segments:
            cache.extend(trigfind.find_trigger_urls(channel, etg, start, end,
                                                    **kwargs))

    # read cache
    trigs = lsctables.New(Table, columns=columns)
    cache.sort(key=lambda x: x.segment[0])
    for segment in segments:
        if len(cache.sieve(segment=segment)):
            if tablename.endswith('_inspiral'):
                filt = lambda t: float(t.get_end()) in segment
            else:
                filt = lambda t: float(t.get_peak()) in segment
            trigs.extend(Table.read(cache.sieve(segment=segment), filt=filt))

    # format table as numpy.recarray
    recarray = trigs.to_recarray(columns=columns)

    # rename columns for convenience later
    if tablename.endswith('_inspiral'):
        tcols = ['end_time', 'end_time_ns']
    elif tablename.endswith('_burst'):
        tcols = ['peak_time', 'peak_time_ns']
        recarray = recfunctions.rename_fields(
            recarray, {'peak_frequency': 'frequency'})
        idx = columns.index('peak_frequency')
        columns.pop(idx)
        columns.insert(idx, 'frequency')
    else:
        tcols = None
    if tcols:
        times = recarray[tcols[0]] + recarray[tcols[1]] * 1e-9
        recarray = recfunctions.rec_append_fields(
            recarray, 'time', times, times.dtype)
        recarray = recfunctions.rec_drop_fields(recarray, tcols)
        columns = ['time'] + columns[2:]
        recarray.sort(order='time')

    # filter
    if snr is not None:
        recarray = recarray[recarray['snr'] >= snr]
    if tablename.endswith('_burst') and frange is not None:
        recarray = recarray[
            (recarray['frequency'] >= frange[0]) &
            (recarray['frequency'] < frange[1])]
    return recarray[columns]


re_delim = re.compile('[_-]')

def find_auxiliary_channels(etg, gps='*', ifo='*', cache=None):
    """Find all auxiliary channels processed by a given ETG
    """
    out = set()
    if cache is not None:
        for e in cache:
            ifo = e.observatory
            name = e.description
            out.add('%s:%s' % (ifo, name.replace('_', '-', 1)))
    else:
        channels = glob.glob(os.path.join(
            trigfind.TRIGFIND_BASE_PATH, '*', ifo, '*', str(gps)[:5]))
        stub = '_%s' % etg.lower()
        for path in channels:
            path = os.path.split(path)[0]
            if not path.lower().endswith('_%s' % etg.lower()):
                continue
            ifo, name = path[:-len(stub)].rsplit(os.path.sep)[-2:]
            out.add('%s:%s' % (ifo, name))
    return sorted(out)


def write_ascii(outfile, recarray, fmt='%s', **kwargs):
    """Write a `numpy.recarray` to file as ASCII

    Parameters
    ----------
    outfile : `str`
        path of output file
    recarray : `numpy.recarray`
        array to write
    fmt : `str`
        format string, or list of format strings

    See Also
    --------
    numpy.savetxt
        for details on the writer, including the `fmt` keyword argument
    """
    kwargs.setdefault('header', ' '.join(recarray.dtype.names))
    numpy.savetxt(outfile, recarray, fmt=fmt, **kwargs)
    return outfile
