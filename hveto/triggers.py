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
import warnings

from six import string_types

import numpy

from glue.lal import Cache

from astropy.table import vstack as vstack_tables

from gwpy.table import EventTable
from gwpy.plotter.table import get_column_string
from gwpy.segments import SegmentList

try:  # use new trigfind module
    import trigfind
except ImportError:
    from gwpy.table.io import trigfind

# -- utilities ----------------------------------------------------------------

COLUMN_LABEL = {
    'peal_frequency': r"Frequency [Hz]",
    'central_freq': r"Frequency [Hz]",
    'frequency': r"Frequency [Hz]",
    'mchirp': r"Chirp mass [M$_\odot$]",
    'new_snr': r"$\chi^2$-weighted signal-to-noise ratio (New SNR)",
    'peak_frequency': r"Frequency [Hz]",
    'rho': r"$\rho$",
    'snr': r"Signal-to-noise ratio (SNR)",
    'template_duration': r"Template duration [s]",
}


def get_column_label(column):
    try:
        return COLUMN_LABEL[column]
    except KeyError:
        return get_column_string(column)


# -- find files/channels ------------------------------------------------------

def find_trigger_files(channel, etg, segments, **kwargs):
    """Find trigger files for a given channel and ETG

    Parameters
    ----------
    channel : `str`
        name of channel to find

    etg : `str`
        name of event trigger generator to find

    segments : :class:`~glue.segments.segmentlist`
        list of segments to find

    **kwargs
        all other keyword arguments are passed to
        `trigfind.find_trigger_urls`

    Returns
    -------
    cache : :class:`~glue.lal.Cache`
        cache of trigger file paths

    See Also
    --------
    trigfind.find_trigger_urls
        for details on file discovery
    """
    cache = Cache()
    for start, end in segments:
        try:
            cache.extend(trigfind.find_trigger_urls(channel, etg, start,
                                                    end, **kwargs))
        except ValueError as e:
            if str(e).lower().startswith('no channel-level directory'):
                warnings.warn(str(e))
            else:
                raise
    return cache.unique()


re_delim = re.compile('[_-]')

def find_auxiliary_channels(etg, gps='*', ifo='*', cache=None):
    """Find all auxiliary channels processed by a given ETG

    If `cache=None` is given (default), the channels are parsed from the
    ETG archive under ``/home/detchar/triggers``. Otherwise, the channel
    names are parsed from the files in the `cache`, assuming they follow
    the T050017 file-naming convention.

    Parameters
    ----------
    etg : `str`
        name of the trigger generator
    gps : `int`, `tuple`, optional
        GPS reference time, or pair of times indicating [start, end),
        at which to find channels
    ifo : `str`, optional
        interferometer prefix for which to find channels
    cache : `~glue.lal.Cache`, optional
        `Cache` of files from which to parse channels

    Returns
    -------
    channels : `list` of `str`
        the names of all available auxiliary channels
    """
    out = set()
    if cache is not None:
        for e in cache:
            ifo = e.observatory
            name = e.description
            channel = '%s:%s' % (ifo, name.replace('_', '-', 1))
            if channel.lower().endswith(etg.lower()):
                channel = channel[:-len(etg)]
            out.add(u'%s' % channel.rstrip('_'))
    else:
        if not isinstance(gps, (list, tuple)):
            gps = (gps, gps)
        gps5 = int(str(gps[0])[:5])
        gpse = int(str(gps[-1])[:5])
        while gps5 <= gpse and gps5 * 1e5 < gps[-1]:
            channels = glob.glob(os.path.join(
                '/home/detchar/triggers', ifo, '*', str(gps5)))
            if len(channels) == 0:  # try old convention
                channels = glob.glob(os.path.join(
                    '/home/detchar/triggers', '*', ifo, '*', str(gps5)))
                use_o2 = False
            else:
                use_o2 = True
            stub = '_%s' % etg.lower()
            for path in channels:
                path = os.path.split(path)[0]
                if not path.lower().endswith('_%s' % etg.lower()):
                    continue
                ifo, name = path[:-len(stub)].rsplit(os.path.sep)[-2:]
                if use_o2:
                    out.add(u'%s:%s' % (ifo, name.replace('_', '-', 1)))
                else:
                    out.add(u'%s:%s' % (ifo, name))
            gps5 += 1
    return sorted(out)


# -- read ---------------------------------------------------------------------

def get_triggers(channel, etg, segments, cache=None, snr=None, frange=None,
                 raw=False, trigfind_kwargs={}, **read_kwargs):
    """Get triggers for the given channel
    """
    # format params
    for key in read_kwargs:
        if (key.endswith(('columns', 'names', 'branches')) and
                isinstance(read_kwargs[key], string_types)):
            read_kwargs[key] = [x.strip(' ') for x in
                                      read_kwargs[key].split(',')]

    # set default columns for sngl_burst table (Omicron)
    if read_kwargs.get('format', '') == 'ligolw.sngl_burst':
        read_kwargs.setdefault('columns', ['peak', 'peak_frequency', 'snr'])
        read_kwargs.setdefault('ligolw_columns', ['peak_time', 'peak_time_ns',
                                                  'peak_frequency', 'snr'])
        read_kwargs.setdefault('get_as_columns', True)

    # hacky fix for reading ASCII
    #    astropy's ASCII reader uses `include_names` and not `columns`
    if read_kwargs.get('format', '').startswith('ascii'):
        read_kwargs.setdefault('include_names',
                               read_kwargs.pop('columns', None))

    # find triggers
    if cache is None:
        cache = find_trigger_files(channel, etg, segments, **trigfind_kwargs)

    # read files
    tables = []
    if len(cache) > 1:
        for segment in segments:
            segaslist = SegmentList([segment])
            segcache = cache.sieve(segment=segment)
            # try and work out if cache overextends segment (so we need to crop)
            try:
                cachesegs = segcache.to_segmentlistdict()[channel[:2]]
            except KeyError:
                outofbounds = False
            else:
                outofbounds = abs(cachesegs - segaslist)
            if segcache:
                if len(segcache) == 1:  # just pass the single filename
                    segcache = segcache[0].path
                new = EventTable.read(segcache, **read_kwargs)
                new.meta = {}  # we never need the metadata
                if outofbounds:
                    new = new[new[new.dtype.names[0]].in_segmentlist(segaslist)]
                tables.append(new)
    elif len(cache) == 1:
        new = EventTable.read(cache[0].path, **read_kwargs)
        new.meta = {}  # we never need the metadata
        new = new[new[new.dtype.names[0]].in_segmentlist(segments)]
        tables.append(new)

    if len(tables):
        table = vstack_tables(tables)
    else:
        table = EventTable(names=read_kwargs.get(
            'columns', ['time', 'frequency', 'snr']))

    # parse time, frequency-like and snr-like column names
    columns = table.dtype.names
    tcolumn = columns[0]
    fcolumn = columns[1]
    scolumn = columns[2]

    # filter
    keep = numpy.ones(len(table), dtype=bool)
    if snr is not None:
        keep &= table[scolumn] >= snr
    if frange is not None:
        keep &= table[fcolumn] >= frange[0]
        keep &= table[fcolumn] < frange[1]
    table = table[keep]

    # return basic table if 'raw'
    if raw:
        return table

    # rename time column so that all tables match in at least that
    table.rename_column(tcolumn, 'time')

    # add channel column to identify all triggers
    table.add_column(table.Column(data=numpy.repeat(channel, len(table)),
                                  name='channel'))

    table.sort('time')
    return table
